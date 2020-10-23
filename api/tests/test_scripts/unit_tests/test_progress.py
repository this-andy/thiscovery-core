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
import api.endpoints.progress_process as prog_proc
import api.endpoints.project as p
import api.endpoints.user_task as ut

TEST_DATA_FOLDER = '../test_data/'


class MyTestCase(test_utils.DbTestCase):

    def test_01_update_cochrane_progress(self):
        """
        This test relies on data from a mock API response. The body returned by that mock API is:
        {
            "records": [
                {
                    "task": "ext-6a",
                    "count": 15,
                    "uuid": "35224bd5-f8a8-41f6-8502-f96e12d6ddde"
                },
                {
                    "task": "ext-6a",
                    "count": 30,
                    "uuid": "8518c7ed-1df4-45e9-8dc4-d49b57ae0663"
                },
                {
                    "task": "ext-5a",
                    "count": 1867,
                    "uuid": "851f7b34-f76c-49de-a382-7e4089b744e2"
                },
                {
                    "task": "ext-5a",
                    "count": 1,
                    "uuid": "d1070e81-557e-40eb-a7ba-b951ddb7ebdc"
                },
                {
                    "task": 1234,
                    "count": 579,
                    "uuid": "d1070e81-557e-40eb-a7ba-b951ddb7ebdc"
                }
            ],
            "daterun": "2019-12-18 12:16:42 UTC",
            "caption": "THIS task summary"
        }
        """
        expected_result = {'updated_project_tasks': 3, 'updated_user_tasks': 5}
        result = prog_proc.update_cochrane_progress(event=None, context=None)
        self.assertEqual(expected_result, result)

        # check project task progress was updated
        for ext_task_id, expected_pt_assessments in [('ext-6a', 45), ('ext-5a', 1868)]:
            pts = p.get_project_task_by_external_task_id(ext_task_id)
            # todo: p.get_project_task_by_external_task_id and p.get_project_task execute very similar SQL queries; could join using a template
            pt = [x for x in pts if x['task_provider_name'] == 'Cochrane'][0]
            pt = p.get_project_task(pt['id'])[0]
            actual_pt_assessments = pt['progress_info']['total assessments']
            self.assertEqual(expected_pt_assessments, actual_pt_assessments)
            expected_pt_progress_modified = '2019-12-18T12:16:42+00:00'
            actual_pt_progress_modified = pt['progress_info_modified']
            self.assertEqual(expected_pt_progress_modified, actual_pt_progress_modified)

        # check user task progress was updated (tip: db view user_tasks_with_anon_ids is the best source for the info below)
        user_tasks_lookup = {
            'ext-6a-35224bd5-f8a8-41f6-8502-f96e12d6ddde': {
                'ut_id': 'ade342a2-a1ec-49fb-ab0f-2f81357cbced',
                'expected_ut_assessments': 15,
            },
            'ext-6a-8518c7ed-1df4-45e9-8dc4-d49b57ae0663': {
                'ut_id': 'd4a47805-fbec-4e43-938c-94af7214326d',
                'expected_ut_assessments': 30,
            },
            'ext-5a-851f7b34-f76c-49de-a382-7e4089b744e2': {
                'ut_id': '3c7978a8-c618-4e39-9ca9-7073faafeb56',
                'expected_ut_assessments': 1867,
            },
            'ext-5a-d1070e81-557e-40eb-a7ba-b951ddb7ebdc': {
                'ut_id': 'ceb30e82-de0f-4009-940d-778dace69ec9',
                'expected_ut_assessments': 1,
            },
        }

        for k, v in user_tasks_lookup.items():
            ut_id = v['ut_id']
            expected_ut_assessments = v['expected_ut_assessments']
            user_task = ut.get_user_task(ut_id, correlation_id=None)[0]
            actual_ut_assessments = user_task['progress_info']['total assessments']
            self.assertEqual(expected_ut_assessments, actual_ut_assessments)
