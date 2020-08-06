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
import api.common.utilities as utils
import testing_utilities as test_utils

from api.local.admin_tasks.task_setup.output_anon_project_specific_user_ids_for_test_group import ProcessManager as OutputAnonIds


class NoTestData(test_utils.DbTestCase):
    """
    Use this class to test admin scripts that do not require loading of additional test data
    """

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


