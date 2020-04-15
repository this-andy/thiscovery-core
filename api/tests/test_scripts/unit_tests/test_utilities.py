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

import common.utilities as utils
import testing_utilities as test_utils

from api.common.utilities import set_running_unit_tests


class TestOther(test_utils.BaseTestCase):
    pass


class TestCreateAnonymousUrlParams(test_utils.BaseTestCase):
    def test_correct_output(self):
        expected_result = '?ext_user_project_id=a0c2668e-60ae-45fc-95e6-50270c0fb6a8&ext_user_task_id=e142fdf0-dea3-4513-9226-a1134037f57f'
        result = utils.create_anonymous_url_params('a0c2668e-60ae-45fc-95e6-50270c0fb6a8', 'e142fdf0-dea3-4513-9226-a1134037f57f', external_task_id=None)
        self.assertEqual(expected_result, result)

        expected_result = '?ext_user_project_id=a0c2668e-60ae-45fc-95e6-50270c0fb6a8&ext_user_task_id=e142fdf0-dea3-4513-9226-a1134037f57f' \
                          '&external_task_id=spam_eggs'
        result = utils.create_anonymous_url_params('a0c2668e-60ae-45fc-95e6-50270c0fb6a8', 'e142fdf0-dea3-4513-9226-a1134037f57f', 'spam_eggs')
        self.assertEqual(expected_result, result)

    def test_invalid_input_params_raises_error(self):
        with self.assertRaises(AssertionError) as err:
            utils.create_anonymous_url_params(None, 'e142fdf0-dea3-4513-9226-a1134037f57f', 'ext_task_id')
        self.assertEqual('ext_user_project_id is null', err.exception.args[0])

        with self.assertRaises(AssertionError) as err:
            utils.create_anonymous_url_params('a0c2668e-60ae-45fc-95e6-50270c0fb6a8', None, 'ext_task_id')
        self.assertEqual('ext_user_task_id is null', err.exception.args[0])

class TestValidateInt(TestCase):

    def test_validate_int_ok(self):
        from api.common.utilities import validate_int
        # self.assertTrue(validate_int, 6)
        i = 7
        self.assertEqual(i, validate_int(i))

    def test_validate_int_fail(self):
        from api.common.utilities import validate_int, DetailedValueError
        self.assertRaises(DetailedValueError, validate_int, 'abc')


class TestValidateUuid(TestCase):
    def test_validate_uuid_ok(self):
        import uuid
        from api.common.utilities import validate_uuid
        uuid_str = str(uuid.uuid4())
        self.assertEqual(uuid_str, validate_uuid(uuid_str))

    def test_validate_uuid_fail_1(self):
        import uuid
        from api.common.utilities import DetailedValueError, validate_uuid
        uuid_str = str(uuid.uuid1())
        self.assertRaises(DetailedValueError, validate_uuid, uuid_str)

    def test_validate_uuid_fail_string(self):
        from api.common.utilities import DetailedValueError, validate_uuid
        uuid_str = 'this is not a uuid'
        self.assertRaises(DetailedValueError, validate_uuid, uuid_str)


class TestValidateUtcDatetime(TestCase):
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


class TestMinimiseWhiteSpace(TestCase):
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
