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
import os
from pprint import pprint

import api.common.pg_utilities as pg_utils
import api.common.sql_queries as sql_q
import api.common.utilities as utils
import testing_utilities as test_utils

from thiscovery_lib.dynamodb_utilities import Dynamodb
from api.common.dev_config import QUALTRICS_TEST_OBJECTS
from api.local.admin_tasks.qualtrics_admin.convert_responses_to_contact_list_input_format import ResponsesToContactListConverter
from api.local.admin_tasks.qualtrics_admin.republish_survey_with_user_specific_links import DistributionLinksGenerator
from api.local.admin_tasks.task_setup.output_anon_project_specific_user_ids_for_test_group import ProcessManager as OutputAnonIds
from api.local.admin_tasks.task_setup.create_user_group_for_follow_up_task import ImportManager as CreateUserGroup


class TestAdminTasksDbAccess(test_utils.DbTestCase):

    def test_01_output_anon_project_specific_user_ids_for_test_group_ok(self):
        pt_4a_id = 'f60d5204-57c1-437f-a085-1943ad9d174f'
        output_anon_ids = OutputAnonIds(project_task_id=pt_4a_id)
        anon_project_specific_user_ids = output_anon_ids.get_anon_project_specific_user_ids()
        expected_apsu_ids = [
            'bfecaf5e-52e5-4307-baa8-7e5208ca3451',
            '3b76f205-762d-4fad-a06f-60f93bfbc5a9',
        ]
        self.assertEqual(3, len(anon_project_specific_user_ids))
        for i in expected_apsu_ids:
            self.assertIn(i, anon_project_specific_user_ids)

    def test_02_output_anon_project_specific_user_ids_for_test_group_invalid_project_task(self):
        with self.assertRaises(utils.ObjectDoesNotExistError) as context:
            OutputAnonIds(project_task_id='feb54083-4685-4747-bd14-05bef3b97bf9')
        err = context.exception
        err_msg = err.args[0]
        self.assertIn('Project task feb54083-4685-4747-bd14-05bef3b97bf9 could not be found', err_msg)

    def test_03_create_user_group_for_follow_up_task_ok(self):
        create_user_group = CreateUserGroup(csvfile_path=os.path.join(test_utils.TEST_DATA_FOLDER, 'qualtrics_responses.csv'))
        user_group_id = create_user_group.set_or_create_user_group(
            interactive_mode=False,
            ug_json={
                'name': 'Test user group 1',
                'short_name': 'TUG 1',
                'url_code': 'test-user-group-1',
            }
        )
        self.assertIsInstance(user_group_id, str)
        self.assertEqual(36, len(user_group_id))

    def test_04_populate_user_group_for_follow_up_task_ok(self):
        paramedics_user_group_id = '06533020-333c-4046-a1c9-40031e160a23'
        create_user_group = CreateUserGroup(csvfile_path=os.path.join(test_utils.TEST_DATA_FOLDER, 'qualtrics_responses.csv'))
        create_user_group.set_or_create_user_group(ug_id=paramedics_user_group_id)
        create_user_group.populate_user_group()
        user_ids_in_group = pg_utils.execute_query(sql_q.SQL_USER_IDS_IN_USER_GROUP, [paramedics_user_group_id], jsonize_sql=False)
        self.assertEqual(16, len(create_user_group.user_ids))
        self.assertCountEqual(create_user_group.user_ids, user_ids_in_group)
        # check output message
        message = create_user_group.output_user_ids_str()
        expected_message = "User_ids for users in user group 06533020-333c-4046-a1c9-40031e160a23:\n\nd1070e81-557e-40eb-a7ba-b951ddb7ebdc;\n" \
                           "851f7b34-f76c-49de-a382-7e4089b744e2;\n851f7b34-f76c-49de-a382-7e4089b744e2;\n8518c7ed-1df4-45e9-8dc4-d49b57ae0663;\n" \
                           "8518c7ed-1df4-45e9-8dc4-d49b57ae0663;\n35224bd5-f8a8-41f6-8502-f96e12d6ddde;\n8518c7ed-1df4-45e9-8dc4-d49b57ae0663;\n" \
                           "35224bd5-f8a8-41f6-8502-f96e12d6ddde;\n1cbe9aad-b29f-46b5-920e-b4c496d42515;\nd1070e81-557e-40eb-a7ba-b951ddb7ebdc;\n" \
                           "8518c7ed-1df4-45e9-8dc4-d49b57ae0663;\n35224bd5-f8a8-41f6-8502-f96e12d6ddde;\n8518c7ed-1df4-45e9-8dc4-d49b57ae0663;\n" \
                           "1cbe9aad-b29f-46b5-920e-b4c496d42515;\n35224bd5-f8a8-41f6-8502-f96e12d6ddde;\n8518c7ed-1df4-45e9-8dc4-d49b57ae0663"
        self.assertEqual(expected_message, message)

    def test_05_generate_distribution_links_for_contact_list(self):
        self.clear_user_specific_urls()
        project_task_id = '4ee70544-6797-4e21-8cec-5653c8d5b234'
        generator = DistributionLinksGenerator(
            survey_id=QUALTRICS_TEST_OBJECTS['unittest-survey-1']['id'],
            contact_list_id=QUALTRICS_TEST_OBJECTS['unittest-contact-list-1']['id'],
            project_task_id=project_task_id,
        )
        generator.generate_links_and_upload_to_dynamodb()
        expected_ddb_keys = [
            f"{project_task_id}_d1070e81-557e-40eb-a7ba-b951ddb7ebdc",
            f"{project_task_id}_851f7b34-f76c-49de-a382-7e4089b744e2",
            f"{project_task_id}_8518c7ed-1df4-45e9-8dc4-d49b57ae0663",
            f"{project_task_id}_35224bd5-f8a8-41f6-8502-f96e12d6ddde",
            f"{project_task_id}_1cbe9aad-b29f-46b5-920e-b4c496d42515",
        ]
        rows = self.ddb_client.scan('UserSpecificUrls')
        keys = [x['id'] for x in rows]
        self.assertCountEqual(expected_ddb_keys, keys)


class TestAdminTasks(test_utils.BaseTestCase):
    def test_05_convert_qualtrics_responses_to_contact_list_import_format_ok(self):
        expected_ids = [
            '1a03cb39-b669-44bb-a69e-98e6a521d758',
            '754d3468-f6f9-46ba-8e30-e29132b925b4',
            'd4714343-305d-40b7-adc1-1b50f5575983',
            '73527dd8-6067-448a-8cd7-481a970a6a13',
            '7e6e4bca-4f0b-4f71-8660-790c1baf3b11',
            '2dc6f2c8-84d9-4705-88e9-d95731c794c9',
            'bfecaf5e-52e5-4307-baa8-7e5208ca3451',
            '922d2b14-554f-42b5-bd20-d024b5ac7214',
            '1406c523-6d12-4510-a745-271ddd9ad3e2',
            '2c8bba57-58a9-4ac7-98e8-beb34f0692c1',
            '82ca200e-66d6-455d-95bc-617f974bcb26',
            'e132c198-06d3-4200-a6c0-cc3bc7991828',
            '87b8f9a8-2400-4259-a8d9-a2f0b16d9ea1',
            'a7a8e630-cb7e-4421-a9b2-b8bad0298267',
            '3b76f205-762d-4fad-a06f-60f93bfbc5a9',
            '64cdc867-e53d-40c9-adda-f0271bcf1063',
        ]
        expected_columns = [
            'LastName', 'FirstName', 'PrimaryEmail', 'ExternalDataReference', 'Q2.2_1', 'Q2.3_1', 'Q2.4_1', 'Q2.5_1', 'Q2.6_1', 'Q2.7_1',
            'Q2.8_1', 'Q2.9_1', 'Q2.10_1', 'Q2.11_1', 'Q2.12_1', 'Q2.13_1', 'Q2.14_1', 'Q2.15_1', 'Q3.1', 'Q4.2',
            'anon_project_specific_user_id'
        ]
        converter = ResponsesToContactListConverter(csvfile_path=os.path.join(test_utils.TEST_DATA_FOLDER, 'qualtrics_responses.csv'))
        result = converter.transform(
            output_temp_file=True
        )
        self.assertEqual(expected_columns, list(result.keys()))
        self.assertEqual(expected_ids, result['ExternalDataReference'])
