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
from api.common.utilities import set_running_unit_tests, DuplicateInsertError, now_with_tz
from api.common.dynamodb_utilities import delete_all, get_table, scan, put_item, get_item, delete_item

TEST_TABLE_NAME = 'testdata'
TIME_TOLERANCE_SECONDS = 10

TEST_ITEM_01 = {
    'key': 'test01',
    'item_type': 'test data',
    'details': {'att1': 'val1', 'att2': 'val2'},
}


def put_test_items(integer):
    """
    Puts "integer" test items in TEST_TABLE_NAME
    :param integer: desired number of test items
    """
    for n in range(integer):
        put_item(TEST_TABLE_NAME, f'test{n:03}', 'test data', {'att1': f'val1.{n}', 'att2': f'val2.{n}'}, {}, True)


class TestDynamoDB(TestCase):

    @classmethod
    def setUpClass(cls):
        set_running_unit_tests(True)

    @classmethod
    def tearDownClass(cls):
        set_running_unit_tests(False)

    def setUp(self):
        delete_all(TEST_TABLE_NAME)

    def common_assertions(self, item, result, relevant_datetime):
        self.assertEqual(item['key'], result['id'])
        self.assertEqual(item['item_type'], result['type'])
        self.assertEqual(item['details'], result['details'])

        # now check relevant datetime - allow up to TIME_TOLERANCE_SECONDS difference
        now = now_with_tz()
        difference = abs(now - relevant_datetime)
        self.assertLess(difference.seconds, TIME_TOLERANCE_SECONDS)

    def test_01_get_table_ok(self):
        table = get_table(TEST_TABLE_NAME)
        items = scan(TEST_TABLE_NAME)
        self.assertEqual('ACTIVE', table.table_status)
        self.assertEqual(0, len(items))

    def test_02_put_and_get_ok(self):
        item = TEST_ITEM_01
        put_item(TEST_TABLE_NAME, item['key'], item['item_type'], item['details'], item, False)
        result = get_item(TEST_TABLE_NAME, item['key'])
        result_created_datetime = parser.parse(result['created'])
        self.common_assertions(item, result, result_created_datetime)

    def test_03_put_update_ok(self):
        item = TEST_ITEM_01
        put_item(TEST_TABLE_NAME, item['key'], item['item_type'], item['details'], item, False)
        item['details'] = {'att1': 'val1', 'att3': 'val3'}
        put_item(TEST_TABLE_NAME, item['key'], item['item_type'], item['details'], item, update_allowed=True)
        result = get_item(TEST_TABLE_NAME, item['key'])
        result_modified_datetime = parser.parse(result['modified'])
        self.common_assertions(item, result, result_modified_datetime)

    def test_04_put_update_fail(self):
        item = TEST_ITEM_01
        put_item(TEST_TABLE_NAME, item['key'], item['item_type'], item['details'], item, False)
        with self.assertRaises(DuplicateInsertError):
            put_item(TEST_TABLE_NAME, item['key'], item['item_type'], item['details'], item, False)

    def test_05_scan(self):
        put_test_items(3)
        items = scan(TEST_TABLE_NAME)
        self.assertEqual(3, len(items))
        self.assertEqual('test002', items[2]['id'])

    def test_06_scan_filter_list(self):
        put_test_items(4)
        items = scan(TEST_TABLE_NAME, 'id', ['test002'])

        self.assertEqual(1, len(items))
        self.assertEqual({'att1': 'val1.2', 'att2': 'val2.2'}, items[0]['details'])

    def test_07_scan_filter_string(self):
        put_test_items(4)
        items = scan(TEST_TABLE_NAME, 'id', 'test002')

        self.assertEqual(1, len(items))
        self.assertEqual({'att1': 'val1.2', 'att2': 'val2.2'}, items[0]['details'])

    def test_08_delete_ok(self):
        put_test_items(1)
        key = 'test000'
        delete_item(TEST_TABLE_NAME, key)
        result = get_item(TEST_TABLE_NAME, key)
        self.assertIsNone(result)
