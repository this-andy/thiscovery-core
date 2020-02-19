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

import json
from http import HTTPStatus

import api.endpoints.progress_process as prog_proc
import api.endpoints.project as p
import api.endpoints.user_task as ut
import common.pg_utilities as pg_utils
import common.sql_queries as sql_q
import testing_utilities as test_utils


class MyTestCase(test_utils.DbTestCase):

    def _check_all_rows_are_expected(self, groups, view_result):
        """
        Args:
            groups (dict or list of dicts): One or more dictionaries representing groups of users and visible projects
            view_result (list): List of all view rows
        """
        unexpected_rows = view_result.copy()
        if isinstance(groups, dict):
            groups = [groups]
        for g in groups:
            for u in g['users']:
                for pr in g['projects']:
                    for r in view_result:
                        if (r['email'] == u) and (r['project_name'] == pr) and (r['group_name'] == g['group_name']):
                            self.logger.debug(f'About to remove an expected row from list of unexpected rows', extra={'expected row': r})
                            unexpected_rows.remove(r)
        self.assertFalse(unexpected_rows)

    def test_01_user_tasks_with_external_ids_length_matches_usertask_table(self):
        view_sql = "SELECT * FROM public.user_tasks_with_external_ids"
        table_sql = "SELECT * FROM public.projects_usertask"
        view_result, table_result = pg_utils.execute_query_multiple((view_sql, table_sql))
        self.assertEqual(len(view_result), len(table_result))

    def test_02_project_group_users(self):
        group_1 = {
            'group_name': 'G1',
            'users': ["clive@email.co.uk", "delia@email.co.uk"],
            'projects': ["PSFU-03-pub-tst-grp", "PSFU-06-prv-act", "PSFU-08-prv-comp"],
        }
        group_2 = {
            'group_name': 'G2',
            'users': ["delia@email.co.uk", "eddie@email.co.uk"],
            'projects': ["PSFU-04-prv-tst-grp", "PSFU-06-prv-act", "PSFU-08-prv-comp"],
        }
        expected_rows = (len(group_1['users']) * len(group_1['projects'])) + (len(group_2['users']) * len(group_2['projects']))

        view_sql = "SELECT * FROM public.project_group_users"
        view_result = pg_utils.execute_query(view_sql)
        self.assertEqual(expected_rows, len(view_result))
        self._check_all_rows_are_expected([group_1, group_2], view_result)

    def test_03_project_testgroup_users(self):
        tester_group = {
            'group_name': 'testers',
            'users': ["bernie@email.co.uk", "clive@email.co.uk", "delia@email.co.uk"],
            'projects': ["PSFU-01-pub-plan", "PSFU-03-pub-tst-grp", "PSFU-04-prv-tst-grp", "PSFU-05-pub-act", "PSFU-06-prv-act"],
        }
        expected_rows = len(tester_group['users']) * len(tester_group['projects'])

        view_sql = "SELECT * FROM public.project_testgroup_users"
        view_result = pg_utils.execute_query(view_sql)
        self.assertEqual(expected_rows, len(view_result))
        self._check_all_rows_are_expected(tester_group, view_result)
