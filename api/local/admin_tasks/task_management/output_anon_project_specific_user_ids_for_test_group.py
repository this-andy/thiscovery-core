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
"""
From User Story 3474:
For testing of stage 2 Delphi surveys, we used to copy user_ids from test group and paste
those into a copy of the Qualtrics Contact List dataset for production. Now that we
are using anon_project_specific_user_ids instead, each test user will have to have a
UserProject for that project in order to have an anon_project_specific_user_id
that we can use.

The goal of this US is to write a admin script to generate UserProjects for
each user in a given UserGroup. It should:
- prompt for a project_task_id corresponding to the task that will be tested
- create one UserProject for each user in that task's test group if the user does not already
have a UserProject
- output a list (csv probably best) of anon_project_specific_user_ids that can be
pasted into the Qualtrics' Contact List spreadsheet.
"""

import csv

import api.endpoints.project as p
import api.endpoints.user_project as up
import api.endpoints.common.pg_utilities as pg_utils
import api.endpoints.common.sql_queries as sq
import thiscovery_lib.utilities as utils


class ProcessManager:

    def __init__(self, project_task_id=None):
        if project_task_id is None:
            self.project_task_id = input("Please enter the project task id:")
        else:
            self.project_task_id = project_task_id
        self.check_project_task_exists()
        self.project_id = pg_utils.execute_query(sq.GET_PROJECT_BY_PROJECT_TASK_ID_SQL, [self.project_task_id], return_json=False)[0][0]
        self.anon_project_specific_user_ids = list()

    def check_project_task_exists(self):
        if not p.get_project_task(self.project_task_id):
            raise utils.ObjectDoesNotExistError(f'Project task {self.project_task_id} could not be found', details={})

    def get_anon_project_specific_user_ids(self):
        users_in_test_group = [x['user_id'] for x in pg_utils.execute_query(sq.TEST_GROUP_USERS_FOR_PROJECT_TASK, [self.project_task_id])]
        counter = 1
        for user_id in users_in_test_group:
            print(f'Processing user {counter} of {len(users_in_test_group)}')
            user_project = up.create_user_project_if_not_exists(user_id, self.project_id)
            self.anon_project_specific_user_ids.append(user_project['anon_project_specific_user_id'])
            counter += 1
        return self.anon_project_specific_user_ids

    def output_anon_project_specific_user_ids(self):
        with open(f'{self.project_task_id}__test_group__anon_project_specific_user_ids.csv', 'w') as csvfile:
            writer = csv.writer(csvfile)
            for anon_id in self.anon_project_specific_user_ids:
                writer.writerow([anon_id])

    def main(self):
        self.get_anon_project_specific_user_ids()
        self.output_anon_project_specific_user_ids()


if __name__ == '__main__':
    manager = ProcessManager()
    manager.main()
