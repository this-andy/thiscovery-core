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
import json
from http import HTTPStatus
from thiscovery_dev_tools.testing_tools import test_get

import api.endpoints.project as p


TEST_SQL_FOLDER = '../test_sql/'
TEST_DATA_FOLDER = '../test_data/'

ENTITY_BASE_URL = 'project'

# region expected bodies setup
PROJECT_01_JSON = """
    {
        "id": "11220597-137d-4452-888d-053f27a78355",
        "name": "PSFU-02-pub-tst-ngrp",
        "short_name": "PSFU-02-pub-tst-ngrp",
        "created": "2018-11-01T21:21:16.280126+00:00",
        "modified": "2018-11-01T21:21:16.280147+00:00",
        "visibility": "public",
        "status": "testing",
        "tasks": [
            {
                "id": "23bdd325-e296-47b3-a38b-8353bac3a984",
                "description": "PSFU-02-A",
                "created": "2018-11-05T12:05:48.724076+00:00",
                "modified": "2018-11-05T12:06:32.725907+00:00",
                "task_type_id": "a5537c85-7d29-4500-9986-ddc18b27d46f",
                "earliest_start_date": null,
                "closing_date": null,
                "signup_status": "not-open",
                "visibility": "public",
                "external_system_id": "e056e0bf-8d24-487e-a57b-4e812b40c4d8",
                "external_task_id": "ext-2a",
                "base_url": "http://crowd.cochrane.org/index.html",
                "status": "testing"
            }
        ]
    }
"""

PROJECT_02_JSON = """
    {
        "id": "a099d03b-11e3-424c-9e97-d1c095f9823b",
        "name": "PSFU-03-pub-tst-grp",
        "short_name": "PSFU-03-pub-tst-grp",
        "created": "2018-11-01T21:21:51.76129+00:00",
        "modified": "2018-11-01T21:21:51.761314+00:00",
        "visibility": "public",
        "status": "testing",
        "tasks": [
            {
                "id": "07af2fbe-5cd1-447f-bae1-3a2f8de82829",
                "description": "PSFU-03-A",
                "created": "2018-11-05T13:53:58.077718+00:00",
                "modified": "2018-11-05T13:53:58.07774+00:00",
                "task_type_id": "a5537c85-7d29-4500-9986-ddc18b27d46f",
                "earliest_start_date": null,
                "closing_date": null,
                "signup_status": "not-open",
                "visibility": "public",
                "external_system_id": "9645a6b1-febb-4c40-8ee4-ff3264cf26af",
                "external_task_id": "ext-3a",
                "base_url": "https://www.qualtrics.com",
                "status": "testing"
            }
        ]
    }
"""

PROJECT_03_JSON = """
    {
        "id": "7c18c259-ace6-4f48-9206-93cd15501348",
        "name": "PSFU-04-prv-tst-grp",
        "short_name": "PSFU-04-prv-tst-grp",
        "created": "2018-11-01T21:22:39.58747+00:00",
        "modified": "2018-11-01T21:22:39.587492+00:00",
        "visibility": "private",
        "status": "testing",
        "tasks": [
            {
                "id": "f60d5204-57c1-437f-a085-1943ad9d174f",
                "description": "PSFU-04-A",
                "created": "2018-11-05T13:55:00.272251+00:00",
                "modified": "2018-11-05T13:55:00.272312+00:00",
                "task_type_id": "a5537c85-7d29-4500-9986-ddc18b27d46f",
                "earliest_start_date": null,
                "closing_date": null,
                "signup_status": "open",
                "visibility": "private",
                "external_system_id": "9645a6b1-febb-4c40-8ee4-ff3264cf26af",
                "external_task_id": "ext-4a",
                "base_url": "https://www.qualtrics.com",
                "status": "testing"
            }
        ]
    }
"""

PROJECT_04_JSON = """
    {
        "id": "5907275b-6d75-4ec0-ada8-5854b44fb955",
        "name": "PSFU-05-pub-act",
        "short_name": "PSFU-05-pub-act",
        "created": "2018-11-01T21:24:48.970756+00:00",
        "modified": "2018-11-01T21:24:48.970787+00:00",
        "visibility": "public",
        "status": "active",
        "tasks": [
            {
                "id": "6cf2f34e-e73f-40b1-99a1-d06c1f24381a",
                "description": "PSFU-05-A",
                "created": "2018-11-05T13:55:53.660935+00:00",
                "modified": "2018-11-05T13:55:53.660956+00:00",
                "task_type_id": "a5537c85-7d29-4500-9986-ddc18b27d46f",
                "earliest_start_date": null,
                "closing_date": null,
                "signup_status": "open",
                "visibility": "public",
                "external_system_id": "e056e0bf-8d24-487e-a57b-4e812b40c4d8",
                "external_task_id": "ext-5a",
                "base_url": "http://crowd.cochrane.org/index.html",
                "status": "active"
            },
            {
                "id": "273b420e-09cb-419c-8b57-b393595dba78",
                "description": "PSFU-05-B",
                "created": "2018-11-05T13:56:52.956515+00:00",
                "modified": "2018-11-05T13:56:52.956539+00:00",
                "task_type_id": "a5537c85-7d29-4500-9986-ddc18b27d46f",
                "earliest_start_date": null,
                "closing_date": null,
                "signup_status": "open",
                "visibility": "private",
                "external_system_id": "9645a6b1-febb-4c40-8ee4-ff3264cf26af",
                "external_task_id": "ext-5b",
                "base_url": "https://www.qualtrics.com",
                "status": "active"
            },
            {
                "id": "b38bcc67-cc01-4e67-9ec0-0ec68b44e306",
                "description": "PSFU-05-C",
                "created": "2018-11-05T13:57:28.162673+00:00",
                "modified": "2018-11-05T13:57:28.162704+00:00",
                "task_type_id": "a5537c85-7d29-4500-9986-ddc18b27d46f",
                "earliest_start_date": null,
                "closing_date": null,
                "signup_status": "not-open",
                "visibility": "public",
                "external_system_id": "9645a6b1-febb-4c40-8ee4-ff3264cf26af",
                "external_task_id": "ext-5c",
                "base_url": "https://www.qualtrics.com",
                "status": "active"
            },
            {
                "id": "0f1af14b-4f1c-4a4b-9d5a-2f991576823b",
                "description": "PSFU-05-D",
                "created": "2020-01-05T13:57:28.162673+00:00",
                "modified": "2020-01-05T13:57:28.162704+00:00",
                "task_type_id": "a5537c85-7d29-4500-9986-ddc18b27d46f",
                "earliest_start_date": null,
                "closing_date": null,
                "signup_status": "open",
                "visibility": "private",
                "external_system_id": "9645a6b1-febb-4c40-8ee4-ff3264cf26af",
                "external_task_id": "ext-5d",
                "base_url": "https://www.qualtrics.com",
                "status": "testing"
            },
            {
                "id": "65569d17-dbdb-4f6c-85e3-6a7e3735deeb",
                "description": "PSFU-05-E",
                "created": "2020-01-06T14:57:28.162673+00:00",
                "modified": "2020-01-06T14:57:28.162704+00:00",
                "task_type_id": "a5537c85-7d29-4500-9986-ddc18b27d46f",
                "earliest_start_date": null,
                "closing_date": null,
                "signup_status": "open",
                "visibility": "public",
                "external_system_id": "9645a6b1-febb-4c40-8ee4-ff3264cf26af",
                "external_task_id": "ext-5e",
                "base_url": "https://www.qualtrics.com",
                "status": "testing"
            }
        ]
    }
"""

PROJECT_05_JSON = """
    {
        "id": "ce36d4d9-d3d3-493f-98e4-04f4b29ccf49",
        "name": "PSFU-06-prv-act",
        "short_name": "PSFU-06-prv-act",
        "created": "2018-11-01T21:25:19.957343+00:00",
        "modified": "2018-11-01T21:25:19.957375+00:00",
        "visibility": "private",
        "status": "active",
        "tasks": [
            {
                "id": "b335c46a-bc1b-4f3d-ad0f-0b8d0826a908",
                "description": "PSFU-06-A",
                "created": "2018-11-05T13:58:07.35628+00:00",
                "modified": "2018-11-05T13:58:07.356304+00:00",
                "task_type_id": "a5537c85-7d29-4500-9986-ddc18b27d46f",
                "earliest_start_date": null,
                "closing_date": null,
                "signup_status": "open",
                "visibility": "private",
                "external_system_id": "e056e0bf-8d24-487e-a57b-4e812b40c4d8",
                "external_task_id": "ext-6a",
                "base_url": "http://crowd.cochrane.org/index.html",
                "status": "active"
            },
            {
                "id": "683598e8-435f-4052-a417-f0f6d808373a",
                "description": "PSFU-06-B",
                "created": "2018-11-05T13:58:41.564792+00:00",
                "modified": "2018-11-05T13:58:41.564816+00:00",
                "task_type_id": "a5537c85-7d29-4500-9986-ddc18b27d46f",
                "earliest_start_date": null,
                "closing_date": null,
                "signup_status": "closed",
                "visibility": "private",
                "external_system_id": "9645a6b1-febb-4c40-8ee4-ff3264cf26af",
                "external_task_id": "ext-6b",
                "base_url": "https://www.qualtrics.com",
                "status": "active"
            },
            {
                "id": "5565a1f4-dca6-4ca2-8f60-2820b5ba949b",
                "description": "PSFU-06-C",
                "created": "2019-11-05T13:58:41.564792+00:00",
                "modified": "2019-11-05T13:58:41.564816+00:00",
                "task_type_id": "a5537c85-7d29-4500-9986-ddc18b27d46f",
                "earliest_start_date": null,
                "closing_date": null,
                "signup_status": "open",
                "visibility": "private",
                "external_system_id": "9645a6b1-febb-4c40-8ee4-ff3264cf26af",
                "external_task_id": "ext-6c",
                "base_url": "https://www.qualtrics.com",
                "status": "testing"
            },
            {
                "id": "4664f880-da31-4c81-a8b5-09a47f96a289",
                "description": "PSFU-06-D",
                "created": "2019-11-06T13:58:41.564792+00:00",
                "modified": "2019-11-06T13:58:41.564816+00:00",
                "task_type_id": "a5537c85-7d29-4500-9986-ddc18b27d46f",
                "earliest_start_date": null,
                "closing_date": null,
                "signup_status": "open",
                "visibility": "public",
                "external_system_id": "9645a6b1-febb-4c40-8ee4-ff3264cf26af",
                "external_task_id": "ext-6d",
                "base_url": "https://www.qualtrics.com",
                "status": "testing"
            }
        ]
    }
"""

PROJECT_06_JSON = """
    {
        "id": "183c23a1-76a7-46c3-8277-501f0740939d",
        "name": "PSFU-07-pub-comp",
        "short_name": "PSFU-07-pub-comp",
        "created": "2018-11-01T21:25:52.222854+00:00",
        "modified": "2018-11-01T21:25:52.222876+00:00",
        "visibility": "public",
        "status": "complete",
        "tasks": [
            {
                "id": "f0e20058-ff5f-4c6a-b4af-da891939db17",
                "description": "PSFU-07-A",
                "created": "2018-11-05T13:59:21.213185+00:00",
                "modified": "2018-11-05T13:59:21.213207+00:00",
                "task_type_id": "a5537c85-7d29-4500-9986-ddc18b27d46f",
                "earliest_start_date": null,
                "closing_date": null,
                "signup_status": "closed",
                "visibility": "public",
                "external_system_id": "9645a6b1-febb-4c40-8ee4-ff3264cf26af",
                "external_task_id": "ext-7a",
                "base_url": "https://www.qualtrics.com",
                "status": "complete"
            }
        ]
    }
"""

PROJECT_07_JSON = """
    {
        "id": "2d03957f-ca35-4f6d-8ec6-1b05ee7d279c",
        "name": "PSFU-08-prv-comp",
        "short_name": "PSFU-08-prv-comp",
        "created": "2018-11-01T21:26:12.339373+00:00",
        "modified": "2018-11-01T21:26:12.339396+00:00",
        "visibility": "private",
        "status": "complete",
        "tasks": [
            {
                "id": "99c155d1-9241-4185-af81-04819a406557",
                "description": "PSFU-08-A",
                "created": "2018-11-05T13:59:47.111638+00:00",
                "modified": "2018-11-05T13:59:47.111661+00:00",
                "task_type_id": "a5537c85-7d29-4500-9986-ddc18b27d46f",
                "earliest_start_date": null,
                "closing_date": null,
                "signup_status": "closed",
                "visibility": "private",
                "external_system_id": "e056e0bf-8d24-487e-a57b-4e812b40c4d8",
                "external_task_id": "ext-8a",
                "base_url": "http://crowd.cochrane.org/index.html",
                "status": "complete"
            }
        ]
    }
"""

PROJECT_08_JSON = """
    {
        "id": "3ffc498f-8add-4448-b452-4fc7f463aa21",
        "name": "CTG Monitoring",
        "short_name": "CTG Monitoring",
        "created": "2018-08-17T12:10:56.084487+00:00",
        "modified": "2018-08-17T12:10:56.119612+00:00",
        "visibility": "public",
        "status": "active",
        "tasks": [
            {
                "id": "c92c8289-3590-4a85-b699-98bc8171ccde",
                "description": "Systematic review for CTG monitoring",
                "created": "2018-08-17T12:10:56.98669+00:00",
                "modified": "2018-08-17T12:10:57.023286+00:00",
                "task_type_id": "86118f6f-15e9-4c4b-970c-4c9f15c4baf6",
                "earliest_start_date": "2018-09-15T12:00:00+00:00",
                "closing_date": "2018-08-17T12:00:00+00:00",
                "signup_status": "not-open",
                "visibility": "public",
                "external_system_id": "e056e0bf-8d24-487e-a57b-4e812b40c4d8",
                "external_task_id": "1234",
                "base_url": "http://crowd.cochrane.org/index.html",
                "status": "active"
            },
            {
                "id": "4ee70544-6797-4e21-8cec-5653c8d5b234",
                "description": "Midwife assessment for CTG monitoring",
                "created": "2018-08-17T12:10:57.074321+00:00",
                "modified": "2018-08-17T12:10:57.111495+00:00",
                "task_type_id": "d92d9935-cb9e-4422-9dbb-65c3423599b1",
                "earliest_start_date": null,
                "closing_date": "2018-08-17T09:30:00+00:00",
                "signup_status": "open",
                "visibility": "public",
                "external_system_id": "9645a6b1-febb-4c40-8ee4-ff3264cf26af",
                "external_task_id": "5678",
                "base_url": "https://www.qualtrics.com",
                "status": "active"
            }
        ]
    }
"""
# endregion


class TestProject(test_utils.DbTestCase):
    maxDiff = None

    def get_project_api_assertions(self, project_id, expected_status=HTTPStatus.OK, correlation_id_in_result=False, expected_body=None, expected_message=None):
        path_parameters = {'id': project_id}

        endpoint = f'v1/{ENTITY_BASE_URL}'
        result = test_get(p.get_project_api, endpoint, path_parameters)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        if correlation_id_in_result:
            self.assertTrue('correlation_id' in result_json)
        if expected_body:
            self.assertDictEqual(expected_body[0], result_json[0])
        if expected_message:
            self.assertTrue('message' in result_json and result_json['message'] == expected_message)

    def test_1_list_projects_api(self):
        expected_status = HTTPStatus.OK
        expected_body = [json.loads(x) for x in [PROJECT_08_JSON, PROJECT_01_JSON, PROJECT_02_JSON, PROJECT_03_JSON, PROJECT_04_JSON, PROJECT_05_JSON,
                                                 PROJECT_06_JSON, PROJECT_07_JSON]]
        result = test_get(p.list_projects_api, f'v1/{ENTITY_BASE_URL}', None, None, None)
        result_status = result['statusCode']
        result_json = json.loads(result['body'])

        self.assertEqual(expected_status, result_status)
        self.assertEqual(len(expected_body), len(result_json))
        for (result, expected) in zip(result_json, expected_body):
            self.assertDictEqual(expected, result)

    def test_2_get_project_api_exists(self):
        self.get_project_api_assertions("a099d03b-11e3-424c-9e97-d1c095f9823b", expected_body=[json.loads(PROJECT_02_JSON)])

    def test_3_get_project_api_not_exists(self):
        self.get_project_api_assertions("0c137d9d-e087-448b-ba8d-24141b6ceece", expected_status=HTTPStatus.NOT_FOUND, correlation_id_in_result=True,
                                        expected_message='project is planned or does not exist')

    def test_4_get_project_api_planned_not_returned(self):
        self.get_project_api_assertions("6b95e66d-1ff8-453a-88ce-ae0dc4b21df9", expected_status=HTTPStatus.NOT_FOUND, correlation_id_in_result=True,
                                        expected_message='project is planned or does not exist')
