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
        from api.common.hubspot import get_hubspot_contact_by_email, delete_hubspot_contact
        if DELETE_TEST_DATA:
            contact = get_hubspot_contact_by_email(TEST_EMAIL_ADDRESS, None)
            if contact is not None:
                contact_hubspot_id = contact['vid']
                delete_hubspot_contact(contact_hubspot_id, None)

        set_running_unit_tests(False)

    def test_01_create_contact_ok(self):
        from api.common.hubspot import post_new_user_to_crm, get_hubspot_contact_by_id, get_contact_property

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

        hubspot_id, is_new = post_new_user_to_crm(user_json, None)

        contact = get_hubspot_contact_by_id(hubspot_id, None)

        self.assertEqual(get_contact_property(contact, 'thiscovery_id'), user_json['id'])
        self.assertEqual(get_contact_property(contact, 'firstname'), user_json['first_name'])
        self.assertEqual(get_contact_property(contact, 'lastname'), user_json['last_name'])
        self.assertEqual(get_contact_property(contact, 'email'), user_json['email'])
        self.assertEqual(get_contact_property(contact, 'country'), user_json['country_name'])

    def test_03_update_contact_ok(self):
        from api.common.hubspot import update_contact_by_email, get_hubspot_contact_by_email, hubspot_timestamp, get_contact_property

        correlation_id = new_correlation_id()
        tsn = hubspot_timestamp(str(now_with_tz()))
        property_name = 'thiscovery_registered_date'
        changes = [
                {"property": property_name, "value": int(tsn)},
            ]
        update_contact_by_email('sw@email.co.uk', changes, correlation_id)

        contact = get_hubspot_contact_by_email(TEST_EMAIL_ADDRESS, correlation_id)
        thiscovery_registered_datestamp = get_contact_property(contact, property_name)

        self.assertEqual(str(tsn), thiscovery_registered_datestamp)

    def test_04_create_tle(self):
        from api.common.hubspot import create_or_update_timeline_event, hubspot_timestamp, get_TLE_type_id, TASK_SIGNUP_TLE_TYPE_NAME, \
            get_hubspot_contact_by_email, get_timeline_event

        correlation_id = new_correlation_id()
        contact = get_hubspot_contact_by_email(TEST_EMAIL_ADDRESS, correlation_id)
        contact_hubspot_id = contact['vid']
        tle_type_id = get_TLE_type_id(TASK_SIGNUP_TLE_TYPE_NAME, correlation_id)
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
            'timestamp': hubspot_timestamp(signup_details['created'])
        }

        create_or_update_timeline_event(tle_details, correlation_id)

        tle = get_timeline_event(tle_type_id, tle_id, correlation_id)

        self.assertEqual(tle['project_id'], 'test_project_id')
        self.assertEqual(tle['project_name'], 'Test Project Name')
        self.assertEqual(tle['objectId'], contact_hubspot_id)
        self.assertEqual(contact_hubspot_id, contact_hubspot_id)
