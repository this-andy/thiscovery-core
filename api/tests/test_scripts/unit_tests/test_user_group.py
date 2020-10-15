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

import testing_utilities as test_utils

from thiscovery_lib.utilities import DetailedValueError

TEST_SQL_FOLDER = '../test_sql/'
TEST_DATA_FOLDER = '../test_data/'


class TestUserGroup(test_utils.DbTestCase):

    def test_01_user_group_get_by_id_exist(self):
        from api.endpoints.user_group import UserGroup

        id = "9cabcdea-8169-4101-87bd-24fd92c9a6da"
        expected_body = {
            "id": id,
            "created": "2018-10-25T11:27:27.545703+00:00",
            "modified": "2018-10-25T11:27:27.545726+00:00",
            "name": "Testers",
            "short_name": "testers",
            "url_code": "test_code",
        }
        ug = UserGroup.get_by_id(id, None)
        ug_dict = ug.to_dict()

        self.assertDictEqual(expected_body, ug_dict)

    def test_02_user_group_get_by_id_not_exists(self):
        from api.endpoints.user_group import UserGroup
        id = "9cabcdea-8169-4101-87bd-24fd92c9a6db"
        ug = UserGroup.get_by_id(id, None)
        self.assertIsNone(ug)

    def test_03_user_group_get_by_url_code_exist(self):
        from api.endpoints.user_group import UserGroup

        url_code = "g2_code"

        expected_body = {
            "id": "03719e6a-f85d-492b-be0f-03ab1927014d",
            "created": "2018-11-01T21:36:47.417859+00:00",
            "modified": "2018-11-01T21:36:47.417882+00:00",
            "name": "G2",
            "short_name": "G2",
            "url_code": url_code,
        }
        ug = UserGroup.get_by_url_code(url_code, None)
        ug_dict = ug.to_dict()

        self.assertDictEqual(expected_body, ug_dict)

    def test_04_user_group_get_by_id_not_exists(self):
        from api.endpoints.user_group import UserGroup
        url_code = "NOT_g2_code"
        ug = UserGroup.get_by_url_code(url_code, None)
        self.assertIsNone(ug)

    def test_05_user_group_create_from_json_basic(self):
        from api.endpoints.user_group import UserGroup
        ug_json = {'name': 'test05 ug'}
        ug = UserGroup.from_json(ug_json, None)
        ug_dict = ug.to_dict()

        self.new_uuid_test_and_remove(ug_dict)
        self.now_datetime_test_and_remove(ug_dict, 'created')
        self.now_datetime_test_and_remove(ug_dict, 'modified')

        expected_body = {
            "name": "test05 ug",
            "short_name": None,
            "url_code": None,
        }
        self.assertDictEqual(expected_body, ug_dict)

    def test_06_user_group_create_from_json_more(self):
        from api.endpoints.user_group import UserGroup
        ug_json = {
            'name': 'test05 ug',
            'short_name': 'ug5',
            'url_code': 'ug5_code',
        }
        ug = UserGroup.from_json(ug_json, None)
        ug_dict = ug.to_dict()

        self.new_uuid_test_and_remove(ug_dict)
        self.now_datetime_test_and_remove(ug_dict, 'created')
        self.now_datetime_test_and_remove(ug_dict, 'modified')

        self.assertDictEqual(ug_json, ug_dict)

    def test_07_user_group_create_from_json_full(self):
        from api.endpoints.user_group import UserGroup
        ug_json = {
            'id': 'b20fcb9c-42c6-4fa6-bf1b-8d7add4d4777',
            'created': '2018-08-21 11:16:56+01:00',
            'modified': '2019-05-21 11:10:34+01:00',
            'name': 'test05 ug',
            'short_name': 'ug5',
            'url_code': 'ug5_code',
        }
        ug = UserGroup.from_json(ug_json, None)
        ug_dict = ug.to_dict()

        self.assertDictEqual(ug_json, ug_dict)


    def test_08_user_group_create_from_json_name_missing(self):
        from api.endpoints.user_group import re
        ug_json = {'short_name': 'ug_no_name'}

        with self.assertRaises(DetailedValueError):
            # UserGroup.from_json(ug_json, None)
            # UserGroup.re()
            re(None)

if __name__ == '__main__':
    pass
