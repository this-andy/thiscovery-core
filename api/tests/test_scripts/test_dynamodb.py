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
from api.common.utilities import set_running_unit_tests


class TestDynamoDB(TestCase):

    @classmethod
    def setUpClass(cls):
        set_running_unit_tests(True)

    @classmethod
    def tearDownClass(cls):
        set_running_unit_tests(False)

    def test_validate_int_ok(self):
        from api.common.utilities import validate_int
        # self.assertTrue(validate_int, 6)
        i = 7
        self.assertEqual(i, validate_int(i))

    def test_validate_int_fail(self):
        from api.common.utilities import validate_int, DetailedValueError
        self.assertRaises(DetailedValueError, validate_int, 'abc')
