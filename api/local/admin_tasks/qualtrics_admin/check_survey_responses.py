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
This script parses csv files of surveys' responses exported from Qualtrics. It checks that none of the
recorded responses belong to users in the test group of a project task
"""
import api.local.dev_config
import api.local.secrets
import csv
import os
import sys
from pprint import pprint
from tkinter import Tk
from tkinter.filedialog import askopenfilename

import api.endpoints.common.pg_utilities as pg_utils
import api.endpoints.common.sql_queries as sql_q
import thiscovery_lib.utilities as utils

from api.local.dev_config import SECRETS_NAMESPACE


class DataCheckManager:

    def __init__(self, user_id_column='user_id', anon_project_specific_user_id_column='anon_project_specific_user_id'):
        self.user_id_column = user_id_column
        self.anon_project_specific_user_id_column = anon_project_specific_user_id_column
        self.project_task_id, self.input_filename = self.prompt_user_for_input_data()
        self.user_group_ids = list()
        self.test_group_ids = list()
        self.logger = utils.get_logger()

    @staticmethod
    def prompt_user_for_input_data():
        project_task_id = input("Please enter the project task id:")
        root = Tk()
        root.withdraw()  # we don't want a full GUI, so keep the root window from appearing
        filename = askopenfilename(
            initialdir=os.path.expanduser('~'),
            title="Please select survey results file",
            filetypes=(("csv files", "*.csv"), ("all files", "*.*"))
        )
        root.destroy()
        return project_task_id, filename

    def get_user_group_ids(self):
        self.user_group_ids = pg_utils.execute_query(
            sql_q.USER_GROUP_FOR_PROJECT_TASK,
            [self.project_task_id],
            jsonize_sql=False
        )
        return self.user_group_ids

    def get_test_group_ids(self):
        self.test_group_ids = pg_utils.execute_query(
            sql_q.TEST_GROUP_USERS_FOR_PROJECT_TASK,
            [self.project_task_id],
            jsonize_sql=False
        )
        return self.test_group_ids

    def check_no_testers_in_data(self):
        users_in_both_groups = list()
        users_in_test_group = list()
        users_in_user_group = list()
        user_ids_in_input_file = list()
        with open(self.input_filename) as csv_f:
            reader = csv.DictReader(csv_f)
            for row in reader:
                user_id = row.get(self.user_id_column)

                if user_id is None:
                    anon_project_specific_user_id = row.get(self.anon_project_specific_user_id_column)
                    try:
                        utils.validate_uuid(anon_project_specific_user_id)
                    except utils.DetailedValueError:
                        self.logger.warning(f'anon_project_specific_user_id "{anon_project_specific_user_id}" not valid; row skipped')
                        continue
                    user_id = pg_utils.execute_query(sql_q.GET_USER_BY_ANON_PROJECT_SPECIFIC_USER_ID_SQL, [str(anon_project_specific_user_id)])[0]['id']

                try:
                    utils.validate_uuid(user_id)
                except utils.DetailedValueError:
                    self.logger.warning(f'User id "{user_id}" not valid; row skipped')
                    continue

                user_ids_in_input_file.append(user_id)
                if (user_id in self.test_group_ids) and (user_id in self.user_group_ids):
                    self.logger.warning(f'User {user_id} is both in user group and in test group for this project task')
                    users_in_both_groups.append(user_id)
                elif user_id in self.test_group_ids:
                    self.logger.error(f'User {user_id} is a tester; they are not in user this project task')
                    users_in_test_group.append(user_id)
                elif user_id in self.user_group_ids:
                    users_in_user_group.append(user_id)
                else:
                    print('user_group_ids:')
                    pprint(self.user_group_ids)
                    print('\ntest_group_ids:')
                    pprint(self.test_group_ids)

                    err_message = f'User id {user_id} could not be found on user group or test group of project task {self.project_task_id}. Are ' \
                                  f'you sure you entered the correct project task id?'
                    raise ValueError(err_message)

            return users_in_both_groups, users_in_test_group, users_in_user_group, user_ids_in_input_file

    @pg_utils.db_connection_handler
    def main(self):
        self.get_user_group_ids()
        self.get_test_group_ids()
        users_in_both_groups, users_in_test_group, users_in_user_group, user_ids_in_input_file = self.check_no_testers_in_data()
        self.logger.debug('User ids in input file', extra={'user_ids_in_input_file': user_ids_in_input_file})
        if not users_in_both_groups and not users_in_test_group:
            print('Everything is OK!')
            print('All users in Qualtrics survey responses file are members of the user group of this project task; '
                  'none are members of the testing group')
        else:
            print('Problems found in input file!')
            if users_in_test_group:
                print('The following users are members of the test group of this project task:')
                pprint(users_in_test_group)
            if users_in_both_groups:
                print('The following users are members of both the user and test groups of this project task:')
                pprint(users_in_both_groups)
            sys.exit(1)


if __name__ == '__main__':
    if SECRETS_NAMESPACE != '/prod/':
        continue_prompt = input(f"SECRETS_NAMESPACE is {SECRETS_NAMESPACE} instead of /prod/ so this will probably fail. "
                                f"Are you sure you want to continue? (y/n)")
        if continue_prompt not in ['Y', 'y']:
            import sys
            sys.exit()
    manager = DataCheckManager()
    manager.main()
