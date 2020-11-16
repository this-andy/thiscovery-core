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
import testing_utilities as test_utils  # this should be the first import; it sets env variables
import copy
import json

from http import HTTPStatus
from pprint import pprint

import thiscovery_lib.utilities as utils

from api.endpoints.transactional_email import TransactionalEmail, send_transactional_email_api, parse_consent_body
from api.tests.test_scripts.unit_tests.test_user import EXPECTED_USER

test_email_dict = {
    "template_name": 'unittests_email_template_1',
    "to_recipient_id": 'd1070e81-557e-40eb-a7ba-b951ddb7ebdc',
    "custom_properties": {
        "project_task_description": "Systematic review for CTG monitoring",
        "project_task_name": "CTG Monitoring",
        "project_results_url": "https://www.thiscovery.org/",
    }
}


class TestTransactionalEmail(test_utils.DbTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.email = TransactionalEmail(email_dict=test_email_dict)

    def test_01_get_template_details_ok(self):
        template = self.email._get_template_details()
        expected_template = {
            "bcc": [
                "thiscovery_dev@email.com"
            ],
            "cc": [
                "this_researcher@email.com"
            ],
            "contact_properties": [

            ],
            "custom_properties": [
                {
                    "name": "project_task_name",
                    "required": True
                },
                {
                    "name": "project_task_description",
                    "required": True
                },
                {
                    "name": "project_results_url",
                    "required": False
                }
            ],
            "from": "Sender Name <sender@hubspot.com>",
            "hs_template_id": "33531457008",
            "id": "unittests_email_template_1"
        }
        self.assertDictEqual(expected_template, template)

    def test_02_get_template_details_not_found(self):
        email_dict = copy.deepcopy(test_email_dict)
        email_dict["template_name"] = 'non_existent_email_template'
        email = TransactionalEmail(email_dict=email_dict)
        with self.assertRaises(utils.ObjectDoesNotExistError) as context:
            email._get_template_details()
        err = context.exception
        err_msg = err.args[0]
        self.assertIn('Template not found', err_msg)

    def test_03_validate_properties_ok(self):
        self.assertTrue(self.email._validate_properties())

    def test_04_validate_properties_missing_required_property(self):
        email_dict = copy.deepcopy(test_email_dict)
        del email_dict['custom_properties']["project_task_description"]
        email = TransactionalEmail(email_dict=email_dict)
        with self.assertRaises(utils.DetailedValueError) as context:
            email._validate_properties()
        err = context.exception
        err_msg = err.args[0]
        self.assertIn('Required custom property project_task_description not found in call body', err_msg)

    def test_05_validate_properties_non_specified_property(self):
        email_dict = copy.deepcopy(test_email_dict)
        email_dict['custom_properties']["unspecified_property"] = "This property is not defined in the template"
        email = TransactionalEmail(email_dict=email_dict)
        self.logger.warning('Email object email_dict', extra={'email_dict': email.email_dict})
        with self.assertRaises(utils.DetailedIntegrityError) as context:
            email._validate_properties()
        err = context.exception
        err_msg = err.args[0]
        self.assertIn('Call custom property unspecified_property is not specified in email template', err_msg)

    def test_06_get_user_by_user_id_ok(self):
        self.assertCountEqual(EXPECTED_USER, self.email._get_user())

    def test_07_get_user_by_anon_project_specific_user_id_ok(self):
        email_dict = email_dict = copy.deepcopy(test_email_dict)
        email_dict["to_recipient_id"] = "2c8bba57-58a9-4ac7-98e8-beb34f0692c1"
        email = TransactionalEmail(email_dict=email_dict)
        self.assertCountEqual(EXPECTED_USER, email._get_user())

    def test_08_get_user_not_found(self):
        email_dict = copy.deepcopy(test_email_dict)
        email_dict["to_recipient_id"] = "49ad25c2-560f-4ed1-8e6f-46debf1f2445"
        email = TransactionalEmail(email_dict=email_dict)
        with self.assertRaises(utils.ObjectDoesNotExistError) as context:
            email._get_user()
        err = context.exception
        err_msg = err.args[0]
        self.assertIn('Recipient id does not match any known user_id or anon_project_specific_user_id', err_msg)

    def test_09_format_properties_to_name_value(self):
        expected_result = [
            {
                "name": "project_task_description",
                "value": "Systematic review for CTG monitoring"
            },
            {
                "name": "project_task_name",
                "value": "CTG Monitoring"
            },
            {
                "name": "project_results_url",
                "value": "https://www.thiscovery.org/"
            }
        ]
        self.assertCountEqual(expected_result, TransactionalEmail._format_properties_to_name_value(test_email_dict['custom_properties']))

    def test_10_send_email_ok(self):
        email_dict = copy.deepcopy(test_email_dict)
        email_dict["to_recipient_id"] = 'dceac123-03a7-4e29-ab5a-739e347b374d'
        email = TransactionalEmail(email_dict=email_dict)
        response = email.send(mock_server=True)
        self.assertEqual(HTTPStatus.OK, response.status_code)

    def test_11_send_email_user_without_hubspot_id(self):
        with self.assertRaises(utils.ObjectDoesNotExistError) as context:
            self.email.send()
        err = context.exception
        err_msg = err.args[0]
        self.assertIn('Recipient does not have a HubSpot id', err_msg)

    def test_12_send_transactional_email_api_locally(self):
        email_dict = copy.deepcopy(test_email_dict)
        email_dict["to_recipient_id"] = 'dceac123-03a7-4e29-ab5a-739e347b374d'
        email_dict["mock_server"] = True
        event = {
            'body': json.dumps(email_dict)
        }
        response = send_transactional_email_api(event, context=None)
        self.assertEqual(HTTPStatus.NO_CONTENT, response['statusCode'])

    def test_13_template_name_missing_from_email_dict(self):
        email_dict = copy.deepcopy(test_email_dict)
        del email_dict['template_name']
        with self.assertRaises(utils.DetailedValueError) as context:
            TransactionalEmail(email_dict=email_dict)
        err = context.exception
        err_msg = err.args[0]
        self.assertIn('template_name must be present in email_dict', err_msg)

    def test_14_recipient_missing_from_email_dict(self):
        email_dict = copy.deepcopy(test_email_dict)
        del email_dict['to_recipient_id']
        with self.assertRaises(utils.DetailedValueError) as context:
            TransactionalEmail(email_dict=email_dict)
        err = context.exception
        err_msg = err.args[0]
        self.assertIn('Either to_recipient_id or to_recipient_email must be present in email_dict', err_msg)

    def test_15_send_email_to_email_address_ok(self):
        email_dict = copy.deepcopy(test_email_dict)
        del email_dict["to_recipient_id"]
        email_dict['to_recipient_email'] = 'thiscovery_dev@email.com'
        email = TransactionalEmail(email_dict=email_dict)
        response = email.send(mock_server=True)
        self.assertEqual(HTTPStatus.OK, response.status_code)

    def test_15_send_email_to_invalid_email_address_fails(self):
        email_dict = copy.deepcopy(test_email_dict)
        del email_dict["to_recipient_id"]
        email_dict['to_recipient_email'] = 'thiscovery_dev@emailcom'
        email = TransactionalEmail(email_dict=email_dict)
        with self.assertRaises(utils.DetailedValueError) as context:
            response = email.send(mock_server=True)
        err = context.exception
        err_msg = err.args[0]
        self.assertIn('to_recipient_email is not a valid email address', err_msg)

    def test_16_consent_email_parse_body_ok(self):
        test_body = {
            'current_date': '2020-11-11T23:27:44+00:00',
            'consent_statements': '{"I can confirm that I have read the information sheet dated October 23rd, '
                                  '2020 (Version 3.1) for the above study. I have had the opportunity to consider '
                                  'the information, ask questions, and have had these satisfactorily answered.":"Yes",'
                                  '"I understand that my participation is voluntary and that I am free to withdraw '
                                  'at any time without giving any reason. I understand that my personal data will '
                                  'only be removed from the study records, if it is practical to do so at the point '
                                  'in time that I contact the researchers.":"No","I understand that my data may '
                                  'be accessed by the research sponsor (the Cambridge University Hospitals '
                                  'NHS Foundation Trust and the University of Cambridge), or the Hospital\'s'
                                  ' Research and Development Office for the purpose of monitoring and audit only.":'
                                  '"Yes","I agree to my interview being digitally recorded.":"No","I agree '
                                  'to take part in the above study.":"Yes","I agree that anonymised quotations'
                                  ' from my interview may be used in reports and publications arising from the '
                                  'study.":"Yes","I agree to be contacted at the end of the study to be '
                                  'invited to a workshop. At this workshop we will focus on the practical, '
                                  'ethical and legal challenges of differential diagnosis and the potential '
                                  'for reform.":"No","I wish to be contacted at the end of the study to be '
                                  'informed of the findings of the study.":"Yes","I understand that the '
                                  'information collected about me may be used to support other research in '
                                  'the future, and may be shared anonymously with other researchers.":"No"}',
            'project_short_name': 'test_project',
            'consent_info_url': 'https://en.wikipedia.org/wiki/Consent'
        }
        expected_result = {
            'consent_info_url': 'https://en.wikipedia.org/wiki/Consent',
            'consent_row_01': 'I can confirm that I have read the information sheet dated '
                              'October 23rd, 2020 (Version 3.1) for the above study. I '
                              'have had the opportunity to consider the information, ask '
                              'questions, and have had these satisfactorily answered.',
            'consent_row_02': 'I understand that my participation is voluntary and that I am '
                              'free to withdraw at any time without giving any reason. '
                              'I understand that my personal data will only be removed '
                              'from the study records, if it is practical to do so at the '
                              'point in time that I contact the researchers.',
            'consent_row_03': 'I understand that my data may be accessed by the research '
                              'sponsor (the Cambridge University Hospitals NHS Foundation '
                              "Trust and the University of Cambridge), or the Hospital's "
                              'Research and Development Office for the purpose of '
                              'monitoring and audit only.',
            'consent_row_04': 'I agree to my interview being digitally recorded.',
            'consent_row_05': 'I agree to take part in the above study.',
            'consent_row_06': 'I agree that anonymised quotations from my interview may '
                              'be used in reports and publications arising from the '
                              'study.',
            'consent_row_07': 'I agree to be contacted at the end of the study to be '
                              'invited to a workshop. At this workshop we will focus on '
                              'the practical, ethical and legal challenges of '
                              'differential diagnosis and the potential for reform.',
            'consent_row_08': 'I wish to be contacted at the end of the study to be '
                              'informed of the findings of the study.',
            'consent_row_09': 'I understand that the information collected about me may '
                              'be used to support other research in the future, and may '
                              'be shared anonymously with other researchers.',
            'consent_value_01': 'Yes',
            'consent_value_02': 'No',
            'consent_value_03': 'Yes',
            'consent_value_04': 'No',
            'consent_value_05': 'Yes',
            'consent_value_06': 'Yes',
            'consent_value_07': 'No',
            'consent_value_08': 'Yes',
            'consent_value_09': 'No',
            'current_date': '2020-11-11T23:27:44+00:00',
            'project_short_name': 'test_project'
        }
        result = parse_consent_body(test_body)
        self.assertDictEqual(expected_result, result)
