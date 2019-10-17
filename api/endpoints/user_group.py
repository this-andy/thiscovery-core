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

import uuid
import json
from http import HTTPStatus

if 'api.endpoints' in __name__:
    from .common.pg_utilities import execute_query
    from .common.utilities import validate_uuid, DetailedValueError
    from .common.entity_base import EntityBase
else:
    from common.pg_utilities import execute_query
    from common.utilities import validate_uuid, DetailedValueError
    from common.entity_base import EntityBase


# todo how best to deal with correlation ids


class UserGroup(EntityBase):
    BASE_SELECT_SQL = '''
      SELECT 
        id, 
        created, 
        modified, 
        name, 
        short_name, 
        url_code
      FROM 
        public.projects_usergroup
        '''

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

        ug = cls(name, short_name, url_code)

        return ug

    @classmethod
    def get_by_id(cls, user_group_id, correlation_id):

        try:
            user_group_id = validate_uuid(user_group_id)
        except DetailedValueError as err:
            err.add_correlation_id(correlation_id)
            raise err

        sql_where_clause = " WHERE id = %s"

        ug_json = execute_query(cls.BASE_SELECT_SQL + sql_where_clause, (str(user_group_id),), correlation_id)
        if len(ug_json) > 0:
            ug_json = ug_json[0]
            return cls.from_json(ug_json, correlation_id)
        else:
            return None

    @classmethod
    def get_by_url_code(cls, url_code, correlation_id):

        sql_where_clause = " WHERE url_code = %s"

        ug_json = execute_query(cls.BASE_SELECT_SQL + sql_where_clause, (str(url_code),), correlation_id)

        if len(ug_json) > 0:
            ug_json = ug_json[0]
            return cls.from_json(ug_json, correlation_id)
        else:
            return None

if __name__ == "__main__":
    ug_json = {
        'name': 'my test UG',
        'short_name': 'myUG',
        'url_code': 'UG001'
    }
    correlation_id = None
    # ug = UserGroup.from_json(ug_json, correlation_id)
    # print(ug.to_json())

    # ug = UserGroup.get_by_id('9cabcdea-8169-4101-87bd-24fd92c9a6da', correlation_id)
    ug = UserGroup.get_by_url_code('ug#2', correlation_id)
    print(ug.to_json())
