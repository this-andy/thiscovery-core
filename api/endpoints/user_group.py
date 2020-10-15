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

import common.pg_utilities as pg_utils
import common.sql_queries as sql_q
from common.pg_utilities import execute_query
from thiscovery_lib.utilities import validate_uuid, DetailedValueError
from common.entity_base import EntityBase


# todo how best to deal with correlation ids


class UserGroup(EntityBase):

    def __init__(self, name, short_name, url_code, ug_json=[], correlation_id=None):
        super().__init__(ug_json, correlation_id)
        self.name = name
        self.short_name = short_name
        self.url_code = url_code

    @classmethod
    def from_json(cls, ug_json, correlation_id):
        """
        Creates new object as specified by JSON.
        :param ug_json: MUST contain: name, may OPTIONALLY include: short_name, url_code, id, created, modified
        :param correlation_id:
        :return: new ug object
        """
        try:
            name = ug_json['name']
            if 'short_name' in ug_json:
                short_name = ug_json['short_name']
            else:
                short_name = None
            if 'url_code' in ug_json:
                url_code = ug_json['url_code']
            else:
                url_code = None
        except DetailedValueError as err:
            err.add_correlation_id(correlation_id)
            raise err
        except KeyError as err:
            error_json = {'parameter': err.args[0], 'correlation_id': str(correlation_id)}
            raise DetailedValueError('mandatory data missing', error_json) from err

        ug = cls(name, short_name, url_code, ug_json, correlation_id)

        return ug

    @classmethod
    def get_by_id(cls, user_group_id, correlation_id):

        try:
            user_group_id = validate_uuid(user_group_id)
        except DetailedValueError as err:
            err.add_correlation_id(correlation_id)
            raise err

        sql_where_clause = " WHERE id = %s"

        ug_json = execute_query(sql_q.USER_GROUP_BASE_SELECT_SQL + sql_where_clause, (str(user_group_id),), correlation_id)
        if len(ug_json) > 0:
            ug_json = ug_json[0]
            return cls.from_json(ug_json, correlation_id)
        else:
            return None

    @classmethod
    def get_by_url_code(cls, url_code, correlation_id):

        sql_where_clause = " WHERE url_code = %s"

        ug_json = execute_query(sql_q.USER_GROUP_BASE_SELECT_SQL + sql_where_clause, (str(url_code),), correlation_id)

        if len(ug_json) > 0:
            ug_json = ug_json[0]
            return cls.from_json(ug_json, correlation_id)
        else:
            return None

    def create(self, correlation_id=None):
        return pg_utils.execute_non_query(
            sql_q.CREATE_USER_GROUP_SQL,
            params=[
                self.id,
                self.created,
                self.modified,
                self.name,
                self.short_name,
                self.url_code,
            ],
            correlation_id=correlation_id
        )


def re(cls):
    error_json = {'parameter': 'err.args[0]', 'correlation_id': str('correlation_id')}
    raise DetailedValueError('just testing', error_json)
