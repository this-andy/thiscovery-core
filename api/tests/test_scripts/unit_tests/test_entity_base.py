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
import testing_utilities as test_utils  # this should be the first import; it sets env variables
import json
from api.endpoints.common.entity_base import EntityBase
from thiscovery_lib.utilities import DetailedValueError
from testing_utilities import BaseTestCase


class TestClass(EntityBase):
    def test_method(self):
        pass


class TestEntityBase(BaseTestCase):

    def test_01_entity_create_from_json_basic(self):
        ug = TestClass()
        ug_dict = ug.to_dict()

        self.new_uuid_test_and_remove(ug_dict)
        self.now_datetime_test_and_remove(ug_dict, 'created')
        self.now_datetime_test_and_remove(ug_dict, 'modified')

    def test_02_entity_create_from_json_with_id(self):
        entity_json = {
            'id': '9207bdab-58c1-46a4-9562-b125766ffd23',
        }

        ug = TestClass(entity_json)
        ug_dict = ug.to_dict()

        self.now_datetime_test_and_remove(ug_dict, 'created')
        self.now_datetime_test_and_remove(ug_dict, 'modified')

        self.assertDictEqual(entity_json, ug_dict)

    def test_03_entity_create_from_json_full(self):
        entity_json = {
            'id': 'c2ea7902-8bfb-4220-b782-8a19a0ca9fb4',
            'created': '2018-08-21 11:16:56+01:00',
            'modified': '2019-05-21 11:10:34+01:00',
        }
        ug = TestClass(entity_json)
        ug_dict = ug.to_dict()

        self.assertDictEqual(entity_json, ug_dict)

    def test_04_entity_create_from_json_bad_id(self):
        entity_json = {
            'id': 'this is not a uuid',
        }

        with self.assertRaises(DetailedValueError):
            TestClass(entity_json)

    def test_05_entity_create_from_json_bad_date(self):
        entity_json = {
            'created': 'this is not a date',
        }

        with self.assertRaises(DetailedValueError):
            TestClass(entity_json)

    def test_06_entity_to_json(self):
        entity_json = {
            'id': 'c2ea7902-8bfb-4220-b782-8a19a0ca9fb4',
            'created': '2018-08-21 11:16:56+01:00',
            'modified': '2019-05-21 11:10:34+01:00',
        }
        ug = TestClass(entity_json)
        ug_json = ug.to_json()
        dict_as_json = json.loads(ug_json)
        self.assertDictEqual(entity_json, dict_as_json)
