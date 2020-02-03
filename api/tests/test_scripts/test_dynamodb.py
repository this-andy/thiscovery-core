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

from dateutil import parser

import testing_utilities as test_utils
from common.utilities import set_running_unit_tests, DetailedValueError, now_with_tz
from common.dynamodb_utilities import delete_all, get_table, scan, put_item, get_item, delete_item, update_item

TEST_TABLE_NAME = 'testdata'
TIME_TOLERANCE_SECONDS = 10

TEST_ITEM_01 = {
    'key': 'test01',
    'item_type': 'test data',
    'details': {'att1': 'val1', 'att2': 'val2'},
}

TEST_ITEM_02 = {
    **TEST_ITEM_01,
    'processing_status': 'new',
    'country_code': 'GB',
}


def put_test_items(integer):
    """
    Puts "integer" test items in TEST_TABLE_NAME
    :param integer: desired number of test items
    """
    for n in range(integer):
        put_item(TEST_TABLE_NAME, f'test{n:03}', 'test data', {'att1': f'val1.{n}', 'att2': f'val2.{n}'}, {}, True)


class TestDynamoDB(test_utils.BaseTestCase):

    def setUp(self):
        delete_all(TEST_TABLE_NAME)

    def common_assertions(self, item, result, relevant_datetime_name):
        self.assertEqual(item['key'], result['id'])
        self.assertEqual(item['item_type'], result['type'])
        self.assertEqual(item['details'], result['details'])
        self.now_datetime_test_and_remove(result, relevant_datetime_name, tolerance=TIME_TOLERANCE_SECONDS)

    def test_01_get_table_ok(self):
        table = get_table(TEST_TABLE_NAME)
        items = scan(TEST_TABLE_NAME)
        self.assertEqual('ACTIVE', table.table_status)
        self.assertEqual(0, len(items))

    def test_02_put_and_get_ok(self):
        item = TEST_ITEM_01
        put_item(TEST_TABLE_NAME, item['key'], item['item_type'], item['details'], item, False)
        result = get_item(TEST_TABLE_NAME, item['key'])
        self.common_assertions(item, result, 'created')

    def test_03_put_update_ok(self):
        item = TEST_ITEM_01
        put_item(TEST_TABLE_NAME, item['key'], item['item_type'], item['details'], item, False)
        item['details'] = {'att1': 'val1', 'att3': 'val3'}
        put_item(TEST_TABLE_NAME, item['key'], item['item_type'], item['details'], item, update_allowed=True)
        result = get_item(TEST_TABLE_NAME, item['key'])
        self.common_assertions(item, result, 'modified')

    def test_04_put_update_fail(self):
        item = TEST_ITEM_01
        put_item(TEST_TABLE_NAME, item['key'], item['item_type'], item['details'], item, False)
        with self.assertRaises(DetailedValueError) as error:
            put_item(TEST_TABLE_NAME, item['key'], item['item_type'], item['details'], item, False)
        self.assertEqual('ConditionalCheckFailedException', error.exception.details['error_code'])

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

    def test_09_update_ok(self):
        item = TEST_ITEM_02
        put_item(TEST_TABLE_NAME, item['key'], item['item_type'], item['details'], item, False)
        item['details'] = {'att1': 'val1', 'att3': 'val3'}
        update_item(TEST_TABLE_NAME, item['key'], {'details': item['details']})
        result = get_item(TEST_TABLE_NAME, item['key'])
        self.common_assertions(item, result, 'modified')
        self.assertEqual(item['country_code'], result['country_code'])
