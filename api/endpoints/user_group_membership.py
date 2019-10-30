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
from http import HTTPStatus

if 'api.endpoints' in __name__:
    from api.common.pg_utilities import execute_non_query, execute_query_multiple
    from api.common.utilities import get_correlation_id, get_logger, error_as_response_body, ObjectDoesNotExistError, get_start_time, get_elapsed_ms, \
        triggered_by_heartbeat, validate_uuid, DetailedValueError, DuplicateInsertError
    from api.common.entity_base import EntityBase
    from .user_group import UserGroup
else:
    from common.pg_utilities import execute_non_query, execute_query_multiple
    from common.utilities import get_correlation_id, get_logger, error_as_response_body, ObjectDoesNotExistError, get_start_time, get_elapsed_ms, \
        triggered_by_heartbeat, validate_uuid, DetailedValueError, DuplicateInsertError
    from common.entity_base import EntityBase
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
            user_id = validate_uuid(ugm_json['user_id'])
            user_group_id = validate_uuid(ugm_json['user_group_id'])
        except DetailedValueError as err:   # uuids are not valid
            err.add_correlation_id(correlation_id)
            raise err
        except KeyError as err:   # mandatory data not present
            error_json = {'parameter': err.args[0], 'correlation_id': str(correlation_id)}
            raise DetailedValueError('mandatory data missing', error_json) from err

        ugm = cls(user_id, user_group_id, ugm_json, correlation_id)

        return ugm

    @classmethod
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
                raise ObjectDoesNotExistError('user group url_code does not exist', errorjson)
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

        sql_user = """
            SELECT id
            FROM public.projects_user
            WHERE id = %s
        """

        sql_user_group = """
            SELECT id
            FROM public.projects_usergroup
            WHERE id = %s
        """

        sql_user_group_membership = """
            SELECT id
            FROM public.projects_usergroupmembership
            WHERE user_id = %s and user_group_id = %s
        """

        results = execute_query_multiple((sql_user, sql_user_group, sql_user_group_membership), ((self.user_id,), (self.user_group_id,), (self.user_id, self.user_group_id)), correlation_id)

        user_data = results[0]
        user_group_data = results[1]
        user_group_membership_data = results[2]

        if len(user_data) == 0:
            errorjson = {'user_id': self.user_id, 'correlation_id': str(correlation_id)}
            raise ObjectDoesNotExistError('user does not exist', errorjson)

        if len(user_group_data) == 0:
            errorjson = {'user_group_id': self.user_group_id, 'correlation_id': str(correlation_id)}
            raise ObjectDoesNotExistError('user group does not exist', errorjson)

        if len(user_group_membership_data) > 0:
            errorjson = {'user_id': self.user_id, 'user_group_id': self.user_group_id, 'correlation_id': str(correlation_id)}
            raise DuplicateInsertError('user group membership already exists', errorjson)

        # if no errors nothing to do, nothing to return, let things carry on...

    def insert_to_db(self, correlation_id):
        # todo ref integrity check
        sql = '''INSERT INTO public.projects_usergroupmembership (
                id,
                created,
                modified,
                user_id,
                user_group_id
            ) VALUES ( %s, %s, %s, %s, %s );'''

        execute_non_query(sql, (self.id, self.created, self.created, self.user_id, self.user_group_id), correlation_id)


def create_user_group_membership_api(event, context):
    start_time = get_start_time()
    logger = get_logger()
    correlation_id = None

    if triggered_by_heartbeat(event):
        logger.info('API call (heartbeat)', extra={'event': event})
        return

    try:
        ugm_json = json.loads(event['body'])
        correlation_id = get_correlation_id(event)
        logger.info('API call', extra={'ugm_json': ugm_json, 'correlation_id': correlation_id, 'event': event})

        ugm = UserGroupMembership.new_from_json(ugm_json, correlation_id)
        # response = {"statusCode": HTTPStatus.CREATED, "body": ugm.to_json()}
        response = {"statusCode": HTTPStatus.CREATED, "body": json.dumps(ugm.to_dict())}

    except DuplicateInsertError as err:
        response = {"statusCode": HTTPStatus.NO_CONTENT, "body": err.as_response_body()}

    except ObjectDoesNotExistError as err:
        response = {"statusCode": HTTPStatus.NOT_FOUND, "body": err.as_response_body()}

    except DetailedValueError as err:
        response = {"statusCode": HTTPStatus.BAD_REQUEST, "body": err.as_response_body()}

    except Exception as ex:
        error_msg = ex.args[0]
        logger.error(error_msg, extra={'correlation_id': correlation_id})
        response = {"statusCode": HTTPStatus.INTERNAL_SERVER_ERROR, "body": error_as_response_body(error_msg, correlation_id)}

    logger.info('API response', extra={'response': response, 'correlation_id': correlation_id, 'elapsed_ms': get_elapsed_ms(start_time)})
    return response


if __name__ == "__main__":
    test_ugm_json = {
        # "created": "2019-08-17 12:26:09.023588+01:00",
        # "id": "11110edd-5fa4-461c-b57c-aaf6b16f6822",
        # "modified": "2019-09-17 12:26:09.023665+01:00",
        'user_id': 'd1070e81-557e-40eb-a7ba-b951ddb7ebdc',
        'user_group_id': 'de1192a0-bce9-4a74-b177-2a209c8deeb4',
    }
    corr_id = None
    # ugm = UserGroupMembership.new_from_json(test_ugm_json, corr_id)
    # print(ugm.to_json())

    ev = {'body': json.dumps(test_ugm_json)}
    print(create_user_group_membership_api(ev, None))
