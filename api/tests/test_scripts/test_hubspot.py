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
from api.common.utilities import set_running_unit_tests, now_with_tz
from api.common.dynamodb_utilities import delete_all

TEST_TABLE_NAME = 'notifications'
TIME_TOLERANCE_SECONDS = 10


class TestHubspot(TestCase):

    @classmethod
    def setUpClass(cls):
        set_running_unit_tests(True)
        delete_all(TEST_TABLE_NAME)

    @classmethod
    def tearDownClass(cls):
        set_running_unit_tests(False)

    def test_01_create_contact(self):
        from api.common.hubspot import post_new_user_to_crm
        from api.common.dynamodb_utilities import scan