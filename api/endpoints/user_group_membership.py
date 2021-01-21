#
#   Thiscovery API - THIS Institute’s citizen science platform
#   Copyright (C) 2019 THIS Institute
#
#   This program is free software: you can redistribute it and/or modify
#   it under the terms of the GNU Affero General Public License as
#   published by the Free Software Foundation, either version 3 of the
#   License, or (at your option) any later version.
#
#   This program is distributed in the hope that it will be useful,
#   but WITHOUT ANY WARRANTY; without even the implied warranty of
#   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#   GNU Affero General Public License for more details.
#
#   A copy of the GNU Affero General Public License is available in the
#   docs folder of this project.  It is also available www.gnu.org/licenses/
#

import json
import thiscovery_lib.utilities as utils
from http import HTTPStatus

import common.pg_utilities as pg_utils
from common.pg_utilities import execute_non_query, execute_query_multiple
from common.sql_queries import SQL_USER, SQL_USER_GROUP, SQL_USER_GROUP_MEMBERSHIP, INSERT_USER_GROUP_MEMBERSHIP_SQL
from thiscovery_lib.entity_base import EntityBase
from user_group import UserGroup

# todo how best to deal with correlation ids


class UserGroupMembership(EntityBase):

    def __init__(self, user_id, user_group_id, ugm_json=None, correlation_id=None):
        super().__init__(ugm_json, correlation_id)
        self.user_id = user_id
        self.user_group_id = user_group_id

    @classmethod
    def from_json(cls, ugm_json, correlation_id):
        """
        Creates new object as specified by JSON.
        Checks that attributes are present but does not check for referential integrity (ie that user and group exist)
        :param ugm_json: MUST contain: user_id, user_group_id, may OPTIONALLY include: id, created, modified
        :param correlation_id:
        :return: new ugm object
        """
        try:
            user_id = utils.validate_uuid(ugm_json['user_id'])
            user_group_id = utils.validate_uuid(ugm_json['user_group_id'])
        except utils.DetailedValueError as err:   # uuids are not valid
            err.add_correlation_id(correlation_id)
            raise err
        except KeyError as err:   # mandatory data not present
            error_json = {'parameter': err.args[0], 'correlation_id': str(correlation_id)}
            raise utils.DetailedValueError('mandatory data missing', error_json) from err

        ugm = cls(user_id, user_group_id, ugm_json, correlation_id)

        return ugm

    @classmethod
    @pg_utils.db_connection_handler
    def new_from_json(cls, ugm_json, correlation_id):
        """
        Full process of creating validating and persisting new membership record.
        Creates new object as specified by JSON, checks that user and group exist and that membership does not currently exist in database
        :param ugm_json: MUST contain: user_id, user_group_id, may OPTIONALLY include: id, created, modified
        :param correlation_id:
        :return: new ugm object, will raise errors for invalid data
        """
        if 'url_code' in ugm_json:
            url_code = ugm_json['url_code']
            user_group = UserGroup.get_by_url_code(url_code, correlation_id)
            if user_group is not None:
                ugm_json['user_group_id'] = user_group.id
            else:  # url_code not found
                errorjson = {'url_code': url_code, 'correlation_id': str(correlation_id)}
                raise utils.ObjectDoesNotExistError('user group url_code does not exist', errorjson)
        try:
            ugm = UserGroupMembership.from_json(ugm_json, correlation_id)
            ugm.validate(correlation_id)
            ugm.insert_to_db(correlation_id)
            return ugm
        except Exception as err:
            raise err

    def validate(self, correlation_id):
        """
        Checks that the ids in self actually exist in database and that self does not already exist
        :return: nothing, but raises errors if not valid
        """
        results = execute_query_multiple(
            base_sql_tuple=(SQL_USER, SQL_USER_GROUP, SQL_USER_GROUP_MEMBERSHIP),
            params_tuple=((self.user_id,), (self.user_group_id,), (self.user_id, self.user_group_id)),
            correlation_id=correlation_id
        )

        user_data = results[0]
        user_group_data = results[1]
        user_group_membership_data = results[2]

        if len(user_data) == 0:
            errorjson = {'user_id': self.user_id, 'correlation_id': str(correlation_id)}
            raise utils.ObjectDoesNotExistError('user does not exist', errorjson)

        if len(user_group_data) == 0:
            errorjson = {'user_group_id': self.user_group_id, 'correlation_id': str(correlation_id)}
            raise utils.ObjectDoesNotExistError('user group does not exist', errorjson)

        if len(user_group_membership_data) > 0:
            errorjson = {'user_id': self.user_id, 'user_group_id': self.user_group_id, 'correlation_id': str(correlation_id)}
            raise utils.DuplicateInsertError('user group membership already exists', errorjson)

        # if no errors nothing to do, nothing to return, let things carry on...

    @pg_utils.db_connection_handler
    def insert_to_db(self, correlation_id=None):
        # todo ref integrity check
        execute_non_query(INSERT_USER_GROUP_MEMBERSHIP_SQL, (self.id, self.created, self.created, self.user_id, self.user_group_id), correlation_id)


@utils.lambda_wrapper
@pg_utils.db_connection_handler
def create_user_group_membership_api(event, context):
    logger = event['logger']
    correlation_id = event['correlation_id']

    try:
        ugm_json = json.loads(event['body'])
        logger.info('API call', extra={'ugm_json': ugm_json, 'correlation_id': correlation_id, 'event': event})

        ugm = UserGroupMembership.new_from_json(ugm_json, correlation_id)
        return {"statusCode": HTTPStatus.CREATED, "body": json.dumps(ugm.to_dict())}

    except utils.DuplicateInsertError:
        return {"statusCode": HTTPStatus.NO_CONTENT, "body": json.dumps({})}
    except utils.ObjectDoesNotExistError as err:
        return utils.log_exception_and_return_edited_api_response(err, HTTPStatus.NOT_FOUND, logger, correlation_id)
    except utils.DetailedValueError as err:
        return utils.log_exception_and_return_edited_api_response(err, HTTPStatus.BAD_REQUEST, logger, correlation_id)
    except Exception as err:
        return utils.log_exception_and_return_edited_api_response(err, HTTPStatus.INTERNAL_SERVER_ERROR, logger, correlation_id)
