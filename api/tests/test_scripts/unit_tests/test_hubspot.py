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
from http import HTTPStatus
from unittest import TestCase

import api.common.hubspot as hs
import api.tests.test_scripts.testing_utilities as test_utils
from api.common.hubspot import HubSpotClient

from api.common.dev_config import TRANSACTIONAL_EMAILS_RECIPIENT
from api.common.utilities import set_running_unit_tests, now_with_tz, new_correlation_id


TIME_TOLERANCE_SECONDS = 10
DELETE_TEST_DATA = True

# region test objects
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

TEST_TLE_TYPE_PROPERTIES = [
    {
        "name": "NumericProperty",
        "label": "Numeric Property",
        "propertyType": "Numeric"
    },
    {
      "name": "company",
      "propertyType": "String",
      "label": "Company Name",
      "objectProperty": "company"
    },
    {
      "name": "size",
      "propertyType": "Enumeration",
      "label": "size",
      "options": [
        {
          "value": "large",
          "label": "Large"
        },
        {
          "value": "medium",
          "label": "Medium"
        },
        {
          "value": "small",
          "label": "Small"
        }
      ]
    },
]
# endregion


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

    def test_contacts_01_create_and_get_contact_ok(self):
        user_json = TEST_USER_01
        hubspot_id, is_new = self.hs_client.post_new_user_to_crm(user_json, None)
        contact = self.hs_client.get_hubspot_contact_by_id(hubspot_id, None)

        self.assertEqual(user_json['id'], self.hs_client.get_contact_property(contact, 'thiscovery_id'))
        self.assertEqual(user_json['first_name'], self.hs_client.get_contact_property(contact, 'firstname'))
        self.assertEqual(user_json['last_name'], self.hs_client.get_contact_property(contact, 'lastname'))
        self.assertEqual(user_json['email'], self.hs_client.get_contact_property(contact, 'email'))
        self.assertEqual(user_json['country_name'], self.hs_client.get_contact_property(contact, 'country'))

        all_contacts = self.hs_client.get_hubspot_contacts()
        self.assertIsInstance(all_contacts, dict)
        all_contacts_emails = [x['identity-profiles'][0]['identities'][0]['value'] for x in all_contacts['contacts']]
        self.assertIn(user_json['email'], all_contacts_emails)

    def test_contacts_02_update_contact_ok(self):
        """
        Tests updates by both email and id
        """
        def get_contact_and_check_timestamp(test_case_instance, expected_registered_date):
            contact = test_case_instance.hs_client.get_hubspot_contact_by_email(user_json['email'], correlation_id)
            thiscovery_registered_datestamp = test_case_instance.hs_client.get_contact_property(contact, property_name)
            test_case_instance.assertEqual(str(expected_registered_date), thiscovery_registered_datestamp)

        user_json = TEST_USER_01
        hs_user_id, _ = self.hs_client.post_new_user_to_crm(user_json, None)
        correlation_id = new_correlation_id()

        self.hs_client.logger.info('Testing contact update by email')
        tsn_0 = hs.hubspot_timestamp(str(now_with_tz()))
        property_name = 'thiscovery_registered_date'
        changes = [
                {"property": property_name, "value": int(tsn_0)},
            ]
        self.hs_client.update_contact_by_email(user_json['email'], changes, correlation_id)
        get_contact_and_check_timestamp(self, tsn_0)

        self.hs_client.logger.info('Testing contact update by hubspot id')
        tsn_1 = hs.hubspot_timestamp(str(now_with_tz()))
        while tsn_1 == tsn_0:  # ensure timestamps are different
            tsn_1 = hs.hubspot_timestamp(str(now_with_tz()))
        changes = [
            {"property": property_name, "value": int(tsn_1)},
        ]
        self.hs_client.update_contact_by_id(hs_user_id, changes, correlation_id)
        get_contact_and_check_timestamp(self, tsn_1)


class TestHubspotClient(TestCase):

    @classmethod
    def setUpClass(cls):
        set_running_unit_tests(True)
        cls.hs_client = HubSpotClient()

    @classmethod
    def tearDownClass(cls):
        set_running_unit_tests(False)

    # region Timeline events tests
    def test_tle_01_create_and_delete_tle_type(self):
        """
        Tests the creation and deletion of timeline event types
        """
        tle_type_id = self.hs_client.create_timeline_event_type(TEST_TLE_TYPE_DEFINITION)
        self.assertIsInstance(tle_type_id, int)
        status_code = self.hs_client.delete_timeline_event_type(tle_type_id)
        self.assertEqual(HTTPStatus.NO_CONTENT, status_code)

    def test_tle_02_get_create_and_delete_tle_type_properties(self):
        """
        Tests getting, creating and deleting timeline event type properties
        """
        expected_properties_names = [x['name'] for x in TEST_TLE_TYPE_PROPERTIES]
        tle_type_id = self.hs_client.create_timeline_event_type(TEST_TLE_TYPE_DEFINITION)
        properties_result = self.hs_client.create_timeline_event_type_properties(tle_type_id, TEST_TLE_TYPE_PROPERTIES)
        fetched_properties = self.hs_client.get_timeline_event_type_properties(tle_type_id)
        self.assertIn(fetched_properties[0]['name'], expected_properties_names)
        for r in properties_result:
            self.assertEqual(HTTPStatus.OK, r.status_code)
            r_json = r.json()
            self.assertIn(r_json['name'], expected_properties_names)
            delete_result = self.hs_client.delete_timeline_event_type_property(tle_type_id=tle_type_id, property_id=r_json['id'])
            self.assertEqual(HTTPStatus.NO_CONTENT, delete_result)
        self.assertEqual(0, len(self.hs_client.get_timeline_event_type_properties(tle_type_id)))
        # cleanup
        self.hs_client.delete_timeline_event_type(tle_type_id)

    def test_tle_03_create_tle(self):
        user_json = TEST_USER_01
        self.hs_client.post_new_user_to_crm(user_json, None)
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
    # endregion

    # region credentials and tokens
    def test_cred_01_get_connection_secret(self):
        cs = self.hs_client.get_hubspot_connection_secret()
        expected_keys = [
            "api-key",
            "app-id",
            "client-id",
            "client-secret",
        ]
        self.assertEqual(expected_keys, list(cs.keys()))

    def test_cred_02_get_new_token_from_hubspot(self):
        old_token = self.hs_client.get_token_from_database()
        expected_keys = [
            "access_token",
            "expires_in",
            "refresh_token",
        ]
        self.assertCountEqual(expected_keys, list(old_token.keys()))

        new_token = self.hs_client.get_new_token_from_hubspot()
        expected_keys += ['app-id']
        self.assertCountEqual(expected_keys, list(new_token.keys()))
        self.assertEqual(len(old_token['access_token']), len(new_token['access_token']))
        self.assertNotEqual(old_token['access_token'], new_token['access_token'])
        self.assertEqual(self.hs_client.app_id, new_token['app-id'])
    # endregion


class TestSingleSendClient(test_utils.BaseTestCase):
    test_custom_properties = [
        {
            "name": "project_task_description",
            "value": "Sounds easy on paper, but setting up the app does take time"
        },
        {
            "name": "project_task_name",
            "value": "Send a transactional email"
        },
        {
            "name": "project_results_url",
            "value": "https://www.thiscovery.org/"
        }
    ]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.hs_client = hs.SingleSendClient(mock_server=True)

    def test_send_email_ok(self):
        result = self.hs_client.send_email(
            template_id=33531457008,
            message={
                "to": TEST_USER_01['email']
            },
            customProperties=self.test_custom_properties
        )
        self.assertEqual(HTTPStatus.OK, result.status_code)
        self.assertEqual('SENT', result.json().get('sendResult'))
