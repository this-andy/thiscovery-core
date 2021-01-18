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
import api.endpoints.common.pg_utilities as pg_utils


class DbViewsTestCase(test_utils.DbTestCase):
    tester_group = {
        'group_name': 'testers',
        'users': ["bernie@email.co.uk", "clive@email.co.uk", "delia@email.co.uk"],
        'projects': [
            "PSFU-01-pub-plan",
            "PSFU-03-pub-tst-grp",
            "PSFU-04-prv-tst-grp",
            "PSFU-05-pub-act",
            "PSFU-06-prv-act",
        ],
        'tasks': [
            "PSFU-03-A",
            "PSFU-04-A",
            "PSFU-05-D",
            "PSFU-05-E",
            "PSFU-06-C",
            "PSFU-06-D",
        ],
    }
    group_1 = {
        'group_name': 'G1',
        'users': ["clive@email.co.uk", "delia@email.co.uk"],
        'projects': ["PSFU-03-pub-tst-grp", "PSFU-06-prv-act", "PSFU-08-prv-comp"],
        'tasks': ["PSFU-03-A", "PSFU-05-B", "PSFU-06-A"],
    }
    group_2 = {
        'group_name': 'G2',
        'users': ["delia@email.co.uk", "eddie@email.co.uk"],
        'projects': ["PSFU-04-prv-tst-grp", "PSFU-06-prv-act", "PSFU-08-prv-comp"],
        'tasks': ["PSFU-04-A", "PSFU-05-C", "PSFU-06-B", "PSFU-08-A"],
    }
    demo_tester_group = {
        'group_name': 'd testers',
        'users': ["bernie@email.co.uk", "clive@email.co.uk", "delia@email.co.uk"],
        'projects': [
            "PSFU-09-demo-pub-plan",
            "PSFU-11-demo-pub-tst-grp",
            "PSFU-12-demo-prv-tst-grp",
            "PSFU-13-demo-pub-act",
            "PSFU-14-demo-prv-act",
        ],
        'tasks': [
            "PSFU-11-A",
            "PSFU-12-A",
            "PSFU-13-D",
            "PSFU-13-E",
            "PSFU-14-C",
            "PSFU-14-D",
        ],
    }
    demo_1 = {
        'group_name': 'D1',
        'users': ["clive@email.co.uk", "delia@email.co.uk"],
        'projects': ["PSFU-11-demo-pub-tst-grp", "PSFU-14-demo-prv-act", "PSFU-16-demo-prv-comp"],
        'tasks': ["PSFU-11-A", "PSFU-13-B", "PSFU-14-A"],
    }
    demo_2 = {
        'group_name': 'D2',
        'users': ["delia@email.co.uk", "eddie@email.co.uk"],
        'projects': ["PSFU-12-demo-prv-tst-grp", "PSFU-14-demo-prv-act", "PSFU-16-demo-prv-comp"],
        'tasks': ["PSFU-12-A", "PSFU-13-C", "PSFU-14-B", "PSFU-16-A"],
    }

    def _common_assertions(self, groups, view_name, view_entity='p'):
        """
        Args:
            groups (dict or list of dicts): One or more dictionaries representing groups of users and visible projects
            view_name (str): Name of the view being tested
            view_entity (str): 'p' if each view row represents a project or 't' if they represent tasks
        """
        if isinstance(groups, dict):
            groups = [groups]

        if view_entity == 'p':
            entity_key = 'projects'
            entity_name_column = 'project_name'
        elif view_entity == 't':
            entity_key = 'tasks'
            entity_name_column = 'description'
        else:
            raise NotImplementedError(f'view_entity must be "p" or "t" (not {view_entity})')

        view_result = pg_utils.execute_query(f"SELECT * FROM public.{view_name}")

        unexpected_rows = view_result.copy()
        for g in groups:
            for u in g['users']:
                for e in g[entity_key]:
                    for r in view_result:
                        if (r['email'] == u) and (r[entity_name_column] == e) and (r['group_name'] == g['group_name']):
                            self.logger.debug(f'About to remove an expected row from list of unexpected rows', extra={
                                'expected row': r
                            })
                            unexpected_rows.remove(r)
        self.assertFalse(unexpected_rows)

    def test_01_user_tasks_with_anon_ids_length_matches_usertask_table(self):
        view_sql = "SELECT * FROM public.user_tasks_with_anon_ids"
        table_sql = "SELECT * FROM public.projects_usertask"
        view_result, table_result = pg_utils.execute_query_multiple((view_sql, table_sql))
        self.assertEqual(len(view_result), len(table_result))

    def test_02_project_group_users(self):
        self._common_assertions(
            groups=[self.group_1, self.group_2, self.demo_1, self.demo_2],
            view_name='project_group_users'
        )

    def test_03_project_testgroup_users(self):
        self._common_assertions(
            groups=[self.tester_group, self.demo_tester_group],
            view_name='project_testgroup_users'
        )

    def test_04_project_group_users(self):
        self._common_assertions(
            groups=[self.group_1, self.group_2, self.demo_1, self.demo_2],
            view_name='projecttask_group_users',
            view_entity='t'
        )

    def test_05_projecttask_testgroup_users(self):
        self._common_assertions(
            groups=[self.tester_group, self.demo_tester_group],
            view_name='projecttask_testgroup_users',
            view_entity='t',
        )
