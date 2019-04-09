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


class TestValidate_int(TestCase):

    def test_validate_int_ok(self):
        from api.common.utilities import validate_int
        # self.assertTrue(validate_int, 6)
        i = 7
        self.assertEqual(i, validate_int(i))

    def test_validate_int_fail(self):
        from api.common.utilities import validate_int, DetailedValueError
        self.assertRaises(DetailedValueError, validate_int, 'abc')


class TestValidate_uuid(TestCase):
    def test_validate_uuid_ok(self):
        import uuid
        from api.common.utilities import validate_uuid
        uuid_str = str(uuid.uuid4())
        self.assertEqual(uuid_str, validate_uuid(uuid_str))

    def test_validate_uuid_fail_1(self):
        import uuid
        from api.common.utilities import validate_uuid, DetailedValueError
        uuid_str = str(uuid.uuid1())
        self.assertRaises(DetailedValueError, validate_uuid, uuid_str)

    def test_validate_uuid_fail_string(self):
        from api.common.utilities import validate_uuid, DetailedValueError
        uuid_str = 'this is not a uuid'
        self.assertRaises(DetailedValueError, validate_uuid, uuid_str)


class TestValidate_utc_datetime(TestCase):
    def test_validate_utc_datetime_ok(self):
        from api.common.utilities import validate_utc_datetime, now_with_tz
        dt = str(now_with_tz())
        self.assertEqual(dt, validate_utc_datetime(dt))

    def test_validate_utc_datetime_fail_us_date(self):
        from api.common.utilities import validate_utc_datetime, DetailedValueError
        dt = '2018-23-06 13:40:13.242219'
        self.assertRaises(DetailedValueError, validate_utc_datetime, dt)

    def test_validate_utc_datetime_fail_time_only(self):
        from api.common.utilities import validate_utc_datetime, DetailedValueError
        dt = '13:40:13.242219'
        self.assertRaises(DetailedValueError, validate_utc_datetime, dt)

    def test_validate_utc_datetime_fail_string(self):
        from api.common.utilities import validate_utc_datetime, DetailedValueError
        dt = 'this is not a datetime'
        self.assertRaises(DetailedValueError, validate_utc_datetime, dt)


class TestMinimise_white_space(TestCase):
    def test_minimise_white_space_change(self):
        from api.common.utilities import minimise_white_space
        str1 = '''hello
            world      world'''
        str2 = 'hello world world'
        self.assertEqual(str2, minimise_white_space(str1))

    def test_minimise_white_space_nochange(self):
        from api.common.utilities import minimise_white_space
        str1 = 'hello world world'
        str2 = 'hello world world'
        self.assertEqual(str2, minimise_white_space(str1))


class TestCountry(TestCase):

    @classmethod
    def setUpClass(cls):
        set_running_unit_tests(True)


    @classmethod
    def tearDownClass(cls):
        set_running_unit_tests(False)


    def test_get_country_name_ok(self):
        from api.common.utilities import get_country_name
        self.assertEqual('France', get_country_name('FR'))
        self.assertEqual('United Kingdom', get_country_name('GB'))


    def test_get_country_name_fail(self):
        from api.common.utilities import get_country_name, DetailedValueError
        self.assertRaises(DetailedValueError, get_country_name, 'ZX')
        self.assertRaises(DetailedValueError, get_country_name, '')
        self.assertRaises(DetailedValueError, get_country_name, 'abcdef')

