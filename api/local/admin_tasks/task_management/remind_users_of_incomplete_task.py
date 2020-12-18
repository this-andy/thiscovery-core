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
This script parses a CSV file containing user identifiers and either creates new a user group in Thiscovery
or populates an existing user group
"""
import api.local.dev_config  # sets env variables
import api.local.secrets  # sets env variables

from thiscovery_lib.core_api_utilities import CoreApiClient

import api.endpoints.common.pg_utilities as pg_utils
import api.endpoints.common.sql_queries as sql_q
import api.endpoints.user as u
from api.local.admin_tasks.admin_tasks_utilities import CsvImporter


class Reminder:

    def __init__(self):
        project_task_id = input("Please enter the id of the project task "
                                     "this reminder is about:")

        self.project_task = pg_utils.execute_query(
            base_sql=sql_q.TASK_REMINDER_SQL,
            params=(project_task_id,)
        )[0]

        csv_import = input("Would you like to import a csv file containing "
                           "anon_project_specific_user_ids? (y/N)")

        if csv_import in ['y', 'Y']:
            importer = CsvImporter(
                anon_project_specific_user_id_column='anon_project_specific_user_id',
                csvfile_path=None
            )
            anon_project_specific_user_ids = importer.output_list_of_anon_project_specific_user_ids()
        else:
            anon_project_specific_user_ids = input(
                "Please paste a list of anon_project_specific_user_ids separated by commas:"
            )

        anon_ids = anon_project_specific_user_ids.split(',')
        self.anon_ids = [x.strip() for x in anon_ids]
        self.users = list()
        for anon_id in anon_ids:
            user = u.get_user_by_anon_project_specific_user_id(anon_id)[0]
            if user:
                self.users.append(user)
            else:
                raise ValueError(f'User {anon_id} could not be found')

        self.core_api_client = CoreApiClient()

    def _get_template_details(self):
        custom_properties_base = {
            'project_short_name': self.project_task.get('project_short_name'),
        }

        if self.project_task['task_type_name'] == 'interview':
            template_name = 'interview_task_reminder'
        else:
            template_name = 'generic_task_reminder'
            custom_properties_base.update(task_short_name=self.project_task.get('task_description'))

        return template_name, custom_properties_base

    def remind_users(self):
        reminded_users = list()
        template_name, custom_properties_base = self._get_template_details()
        for user in self.users:
            user_id = user['id']
            email_dict = {
                "to_recipient_id": user_id,
                "custom_properties": {
                    **custom_properties_base,
                    "user_first_name": user['first_name'],
                }
            }
            try:
                self.core_api_client.send_transactional_email(
                    template_name=template_name,
                    **email_dict
                )
            except AssertionError:
                print(f'The following users were reminded before an error occurred:\n'
                      f'{reminded_users}')
                raise
            else:
                reminded_users.append(user_id)


@pg_utils.db_connection_handler
def main():
    reminder = Reminder()
    reminder.remind_users()


if __name__ == '__main__':
    main()
