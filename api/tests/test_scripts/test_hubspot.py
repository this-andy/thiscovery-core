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

import api.common.hubspot as hs

from unittest import TestCase
from api.common.utilities import set_running_unit_tests, now_with_tz, new_correlation_id

TIME_TOLERANCE_SECONDS = 10
TEST_EMAIL_ADDRESS = 'sw@email.co.uk'
DELETE_TEST_DATA = True


class TestHubspot(TestCase):

    @classmethod
    def setUpClass(cls):
        set_running_unit_tests(True)

    @classmethod
    def tearDownClass(cls):
        if DELETE_TEST_DATA:
            contact = hs.get_hubspot_contact_by_email(TEST_EMAIL_ADDRESS, None)
            if contact is not None:
                contact_hubspot_id = contact['vid']
                hs.delete_hubspot_contact(contact_hubspot_id, None)

        set_running_unit_tests(False)

    def test_01_create_contact_ok(self):
        user_json = {
            "id": "48e30e54-b4fc-4303-963f-2943dda2b139",
            "created": "2019-06-01T11:16:56+01:00",
            "email": TEST_EMAIL_ADDRESS,
            "first_name": "Steven",
            "last_name": "Walcorn",
            "thiscovery_id": "d5897775-adbc-4859-b883-1aec0e2fd559",
            "country_code": "GB",
            "country_name": "United Kingdom",
            "status": "new"}

        hubspot_id, is_new = hs.post_new_user_to_crm(user_json, None)

        contact = hs.get_hubspot_contact_by_id(hubspot_id, None)

        self.assertEqual(user_json['id'], hs.get_contact_property(contact, 'thiscovery_id'))
        self.assertEqual(user_json['first_name'], hs.get_contact_property(contact, 'firstname'))
        self.assertEqual(user_json['last_name'], hs.get_contact_property(contact, 'lastname'))
        self.assertEqual(user_json['email'], hs.get_contact_property(contact, 'email'))
        self.assertEqual(user_json['country_name'], hs.get_contact_property(contact, 'country'))

    def test_03_update_contact_ok(self):
        correlation_id = new_correlation_id()
        tsn = hs.hubspot_timestamp(str(now_with_tz()))
        property_name = 'thiscovery_registered_date'
        changes = [
                {"property": property_name, "value": int(tsn)},
            ]
        hs.update_contact_by_email('sw@email.co.uk', changes, correlation_id)

        contact = hs.get_hubspot_contact_by_email(TEST_EMAIL_ADDRESS, correlation_id)
        thiscovery_registered_datestamp = hs.get_contact_property(contact, property_name)

        self.assertEqual(str(tsn), thiscovery_registered_datestamp)

    def test_04_create_tle(self):
        correlation_id = new_correlation_id()
        contact = hs.get_hubspot_contact_by_email(TEST_EMAIL_ADDRESS, correlation_id)
        contact_hubspot_id = contact['vid']
        tle_type_id = hs.get_TLE_type_id(hs.TASK_SIGNUP_TLE_TYPE_NAME, correlation_id)
        tle_id = 'test_tle_01'

        signup_details = {
            'id': tle_id,
            'crm_id': contact_hubspot_id,
            'project_id': 'test_project_id',
            'project_name': 'Test Project Name',
            'task_id': 'test_task_id',
            'task_name': 'Test Task Name',
            'signup_event_type': 'Testing',
            'created': '2015-05-26T17:30:00+01:00'
        }

        tle_details = {
            'id': signup_details['id'],
            'objectId': signup_details['crm_id'],
            'eventTypeId': tle_type_id,
            'project_id': signup_details['project_id'],
            'project_name': signup_details['project_name'],
            'task_id': signup_details['task_id'],
            'task_name': signup_details['task_name'],
            'signup_event_type': signup_details['signup_event_type'],
            'timestamp': hs.hubspot_timestamp(signup_details['created'])
        }

        hs.create_or_update_timeline_event(tle_details, correlation_id)

        tle = hs.get_timeline_event(tle_type_id, tle_id, correlation_id)

        self.assertEqual('test_project_id', tle['project_id'])
        self.assertEqual('Test Project Name', tle['project_name'])
        self.assertEqual(contact_hubspot_id, tle['objectId'])
