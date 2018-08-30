from unittest import TestCase


class TestValidate_int(TestCase):

    def test_validate_int_ok(self):
        from api.utilities import validate_int
        # self.assertTrue(validate_int, 6)
        i = 7
        self.assertEqual(i, validate_int(i))

    def test_validate_int_fail(self):
        from api.utilities import validate_int, DetailedValueError
        self.assertRaises(DetailedValueError, validate_int, 'abc')


class TestValidate_uuid(TestCase):
    def test_validate_uuid_ok(self):
        import uuid
        from api.utilities import validate_uuid
        uuid_str = str(uuid.uuid4())
        self.assertEqual(uuid_str, validate_uuid(uuid_str))

    def test_validate_uuid_fail_1(self):
        import uuid
        from api.utilities import validate_uuid, DetailedValueError
        uuid_str = str(uuid.uuid1())
        self.assertRaises(DetailedValueError, validate_uuid, uuid_str)

    def test_validate_uuid_fail_string(self):
        from api.utilities import validate_uuid, DetailedValueError
        uuid_str = 'this is not a uuid'
        self.assertRaises(DetailedValueError, validate_uuid, uuid_str)


class TestValidate_utc_datetime(TestCase):
    def test_validate_utc_datetime_ok(self):
        import datetime
        from api.utilities import validate_utc_datetime, now_with_tz
        dt = str(now_with_tz())
        self.assertEqual(dt, validate_utc_datetime(dt))

    def test_validate_utc_datetime_fail_us_date(self):
        from api.utilities import validate_utc_datetime, DetailedValueError
        dt = '2018-23-06 13:40:13.242219'
        self.assertRaises(DetailedValueError, validate_utc_datetime, dt)

    def test_validate_utc_datetime_fail_time_only(self):
        from api.utilities import validate_utc_datetime, DetailedValueError
        dt = '13:40:13.242219'
        self.assertRaises(DetailedValueError, validate_utc_datetime, dt)

    def test_validate_utc_datetime_fail_string(self):
        from api.utilities import validate_utc_datetime, DetailedValueError
        dt = 'this is not a datetime'
        self.assertRaises(DetailedValueError, validate_utc_datetime, dt)


class TestMinimise_white_space(TestCase):
    def test_minimise_white_space_change(self):
        from api.utilities import minimise_white_space
        str1 = '''hello
            world      world'''
        str2 = 'hello world world'
        self.assertEqual(str2, minimise_white_space(str1))

    def test_minimise_white_space_nochange(self):
        from api.utilities import minimise_white_space
        str1 = 'hello world world'
        str2 = 'hello world world'
        self.assertEqual(str2, minimise_white_space(str1))