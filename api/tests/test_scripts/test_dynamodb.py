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

from unittest import TestCase
from dateutil import parser
from api.common.utilities import set_running_unit_tests, DuplicateInsertError
from api.common.dynamodb_utilities import delete_all

TEST_TABLE_NAME = 'testdata'
TIME_TOLERANCE_SECONDS = 10


class TestDynamoDB(TestCase):

    @classmethod
    def setUpClass(cls):
        set_running_unit_tests(True)
        delete_all(TEST_TABLE_NAME)

    @classmethod
    def tearDownClass(cls):
        set_running_unit_tests(False)

    def test_01_get_table_ok(self):
        from api.common.dynamodb_utilities import get_table, scan
        table = get_table(TEST_TABLE_NAME)
        items = scan(TEST_TABLE_NAME)

        self.assertEqual('ACTIVE', table.table_status)
        self.assertEqual(0, len(items))

    def test_02_put_and_get_ok(self):
        from api.common.dynamodb_utilities import put_item, get_item
        from api.common.utilities import now_with_tz

        item = {}
        key = 'test01'
        item_type = 'test data'
        details = {'att1': 'val1', 'att2': 'val2'}

        put_item(TEST_TABLE_NAME, key, item_type, details, item, False)
        result = get_item(TEST_TABLE_NAME, key)

        self.assertEqual(key, result['id'])
        self.assertEqual(item_type, result['type'])
        self.assertEqual(details, result['details'])

        # now check modified datetime - allow up to TIME_TOLERANCE_SECONDS difference
        now = now_with_tz()
        result_created_datetime = parser.parse(result['created'])
        difference = abs(now - result_created_datetime)
        self.assertLess(difference.seconds, TIME_TOLERANCE_SECONDS)

    def test_03_put_update_ok(self):
        from api.common.dynamodb_utilities import put_item, get_item
        from api.common.utilities import now_with_tz

        item = {}
        key = 'test01'
        item_type = 'test data'
        details = {'att1': 'val1', 'att3': 'val3'}

        put_item(TEST_TABLE_NAME, key, item_type, details, item, True)
        result = get_item(TEST_TABLE_NAME, key)

        self.assertEqual(key, result['id'])
        self.assertEqual(item_type, result['type'])
        self.assertEqual(details, result['details'])

        # now check modified datetime - allow up to TIME_TOLERANCE_SECONDS difference
        now = now_with_tz()
        result_modified_datetime = parser.parse(result['modified'])
        difference = abs(now - result_modified_datetime)
        self.assertLess(difference.seconds, TIME_TOLERANCE_SECONDS)

    def test_04_put_update_fail(self):
        from api.common.dynamodb_utilities import put_item

        item = {}
        key = 'test01'
        item_type = 'test data'
        details = {'att1': 'val1', 'att2': 'val2'}

        with self.assertRaises(DuplicateInsertError):
            put_item(TEST_TABLE_NAME, key, item_type, details, item, False)

    def test_05_scan(self):
        from api.common.dynamodb_utilities import put_item, scan

        put_item(TEST_TABLE_NAME, 'test02', 'test data', {'att1': 'val1.2', 'att2': 'val2.2'}, {}, True)
        put_item(TEST_TABLE_NAME, 'test03', 'test data', {'att1': 'val1.3', 'att2': 'val2.3'}, {}, True)
        put_item(TEST_TABLE_NAME, 'test04', 'test data', {'att1': 'val1.4', 'att2': 'val2.4'}, {}, True)

        items = scan(TEST_TABLE_NAME)

        self.assertEqual(4, len(items))
        self.assertEqual('test04', items[3]['id'])

    def test_06_scan_filter_list(self):
        from api.common.dynamodb_utilities import scan

        items = scan(TEST_TABLE_NAME, 'id', ['test03'])

        self.assertEqual(1, len(items))
        self.assertEqual({'att1': 'val1.3', 'att2': 'val2.3'}, items[0]['details'])

    def test_07_scan_filter_string(self):
        from api.common.dynamodb_utilities import scan

        items = scan(TEST_TABLE_NAME, 'id', 'test04')

        self.assertEqual(1, len(items))
        self.assertEqual({'att1': 'val1.4', 'att2': 'val2.4'}, items[0]['details'])

    def test_08_delete_ok(self):
        from api.common.dynamodb_utilities import delete_item, get_item

        key = 'test01'
        delete_item(TEST_TABLE_NAME, key)
        result = get_item(TEST_TABLE_NAME, key)

        self.assertIsNone(result)
