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
from api.common.hubspot import HubSpotClient

from http import HTTPStatus
from unittest import TestCase
from api.common.utilities import set_running_unit_tests, now_with_tz, new_correlation_id

TIME_TOLERANCE_SECONDS = 10
DELETE_TEST_DATA = True

TEST_USER_01 = {
    "id": "48e30e54-b4fc-4303-963f-2943dda2b139",
    "created": "2019-06-01T11:16:56+01:00",
    "email": "sw@email.co.uk",
    "first_name": "Steven",
    "last_name": "Walcorn",
    "thiscovery_id": "d5897775-adbc-4859-b883-1aec0e2fd559",
    "country_code": "GB",
    "country_name": "United Kingdom",
    "status": "new"
}

TEST_TLE_TYPE_DEFINITION = {
    "name": "Test timeline type",
    "objectType": "CONTACT",
    "headerTemplate": "# Title for event {{id}}\nThis is an event for {{objectType}}"
}


def delete_test_users(test_users=[TEST_USER_01], hs_client=None):
    if hs_client is None:
        hs_client = HubSpotClient()
    for user in test_users:
        u_email = user['email']
        contact = hs_client.get_hubspot_contact_by_email(u_email, None)
        if contact is not None:
            contact_hubspot_id = contact['vid']
            hs_client.delete_hubspot_contact(contact_hubspot_id, None)


class TestHubspotContacts(TestCase):

    @classmethod
    def setUpClass(cls):
        set_running_unit_tests(True)
        cls.hs_client = HubSpotClient()

    @classmethod
    def tearDownClass(cls):
        if DELETE_TEST_DATA:
            delete_test_users(hs_client=cls.hs_client)
        set_running_unit_tests(False)

    def setUp(self):
        """
        Deletes test_users before each test is run to ensure tests are independent
        """
        delete_test_users(hs_client=self.hs_client)

    def test_01_create_contact_ok(self):
        user_json = TEST_USER_01
        hubspot_id, is_new = hs.post_new_user_to_crm(user_json, None)
        contact = self.hs_client.get_hubspot_contact_by_id(hubspot_id, None)

        self.assertEqual(user_json['id'], self.hs_client.get_contact_property(contact, 'thiscovery_id'))
        self.assertEqual(user_json['first_name'], self.hs_client.get_contact_property(contact, 'firstname'))
        self.assertEqual(user_json['last_name'], self.hs_client.get_contact_property(contact, 'lastname'))
        self.assertEqual(user_json['email'], self.hs_client.get_contact_property(contact, 'email'))
        self.assertEqual(user_json['country_name'], self.hs_client.get_contact_property(contact, 'country'))

    def test_03_update_contact_ok(self):
        user_json = TEST_USER_01
        hs.post_new_user_to_crm(user_json, None)
        correlation_id = new_correlation_id()
        tsn = hs.hubspot_timestamp(str(now_with_tz()))
        property_name = 'thiscovery_registered_date'
        changes = [
                {"property": property_name, "value": int(tsn)},
            ]
        self.hs_client.update_contact_by_email(user_json['email'], changes, correlation_id)

        contact = self.hs_client.get_hubspot_contact_by_email(user_json['email'], correlation_id)
        thiscovery_registered_datestamp = self.hs_client.get_contact_property(contact, property_name)

        self.assertEqual(str(tsn), thiscovery_registered_datestamp)


class TestHubspotTimelineEvents(TestCase):

    @classmethod
    def setUpClass(cls):
        set_running_unit_tests(True)
        cls.hs_client = HubSpotClient()

    @classmethod
    def tearDownClass(cls):
        set_running_unit_tests(False)

    def test_tle_01_create_and_delete_tle_type(self):
        """
        Tests the creation and deletion of timeline event types
        """
        tle_type_id = self.hs_client.create_timeline_event_type(TEST_TLE_TYPE_DEFINITION)
        self.assertIsInstance(tle_type_id, int)
        status_code = self.hs_client.delete_timeline_event_type(tle_type_id)
        self.assertEqual(HTTPStatus.NO_CONTENT, status_code)

    def test_tle_02_create_tle(self):
        user_json = TEST_USER_01
        hs.post_new_user_to_crm(user_json, None)
        correlation_id = new_correlation_id()
        contact = self.hs_client.get_hubspot_contact_by_email(user_json['email'], correlation_id)
        contact_hubspot_id = contact['vid']
        tle_type_id = self.hs_client.get_timeline_event_type_id(hs.TASK_SIGNUP_TLE_TYPE_NAME, correlation_id)
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

        self.hs_client.create_or_update_timeline_event(tle_details, correlation_id)

        tle = self.hs_client.get_timeline_event(tle_type_id, tle_id, correlation_id)

        self.assertEqual('test_project_id', tle['project_id'])
        self.assertEqual('Test Project Name', tle['project_name'])
        self.assertEqual(contact_hubspot_id, tle['objectId'])


class TestHubspotClient(TestCase):

    @classmethod
    def setUpClass(cls):
        set_running_unit_tests(True)
        cls.hs_client = HubSpotClient()

    @classmethod
    def tearDownClass(cls):
        set_running_unit_tests(False)

    def test_client_01_get_connection_secret(self):
        cs = self.hs_client.get_hubspot_connection_secret()
        expected_keys = [
            "api-key",
            "app-id",
            "client-id",
            "client-secret",
        ]
        self.assertEqual(expected_keys, list(cs.keys()))

    def test_client_02_get_new_token_from_hubspot(self):
        old_token = self.hs_client.get_token_from_database()
        expected_keys = [
            "access_token",
            "expires_in",
            "refresh_token",
        ]
        self.assertEqual(expected_keys, sorted(list(old_token.keys())))

        new_token = self.hs_client.get_new_token_from_hubspot()
        expected_keys += ['app-id']
        expected_keys.sort()
        self.assertEqual(expected_keys, sorted(list(new_token.keys())))
        self.assertEqual(len(old_token['access_token']), len(new_token['access_token']))
        self.assertNotEqual(old_token['access_token'], new_token['access_token'])
        self.assertEqual(self.hs_client.app_id, new_token['app-id'])

