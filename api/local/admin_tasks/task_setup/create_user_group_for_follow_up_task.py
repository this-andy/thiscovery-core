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
import api.endpoints.common.pg_utilities as pg_utils
import api.endpoints.common.sql_queries as sql_q
from api.endpoints.user_group import UserGroup
from api.endpoints.user_group_membership import UserGroupMembership
from api.local.admin_tasks.admin_tasks_utilities import CsvImporter


class ImportManager(CsvImporter):

    def __init__(self, anon_project_specific_user_id_column='anon_project_specific_user_id', csvfile_path=None):
        self.user_group_id = None
        self.added_user_ids = list()
        super().__init__(anon_project_specific_user_id_column, csvfile_path=csvfile_path)
        super().validate_input_file_and_get_users()

    def set_or_create_user_group(self, ug_id=None, ug_json=None, interactive_mode=True):
        """

        Args:
            ug_id:
            ug_json (dict): must be provided if interactive_mode is False; overwritten if interactive_mode is True
            interactive_mode:

        Returns:

        """
        print(f'Found {len(self.user_ids)} users in input file. User ids are: {self.user_ids}')

        if ug_id is not None:
            self.user_group_id = ug_id
            return self.user_group_id

        else:
            if interactive_mode:
                ug_id = input('Please enter the id of the user group you would like to populate (or leave blank to create a new group):')
                if ug_id:
                    self.user_group_id = ug_id
                    return self.user_group_id
                else:
                    group_name = input('Please enter the new user group name:')
                    group_short_name = input('Please enter the new user group short name:')
                    group_code = input('Please enter the new user group url code:')
                    ug_json = {
                        'name': group_name,
                        'short_name': group_short_name,
                        'url_code': group_code,
                    }

            ug = UserGroup.from_json(ug_json, None)
            self.user_group_id = ug.to_dict()['id']
            ug.create()
            print(f'Created new user group with id {self.user_group_id}')
            return self.user_group_id

    def get_current_membership(self):
        user_ids_in_group = pg_utils.execute_query(
            base_sql=sql_q.SQL_USER_IDS_IN_USER_GROUP,
            params=[self.user_group_id],
            jsonize_sql=False
        )
        return user_ids_in_group

    def populate_user_group(self):
        user_ids_in_group = self.get_current_membership()
        ugm_list = list()
        for user_id in self.user_ids:
            if user_id not in user_ids_in_group:
                ugm_json = {
                    'user_id': user_id,
                    'user_group_id': self.user_group_id,
                }
                ugm = UserGroupMembership.from_json(ugm_json, None)
                ugm.insert_to_db()
                ugm_id = ugm.to_dict()['id']
                ugm_list.append(ugm_id)
                self.added_user_ids.append(user_id)
        print(f'Added {len(ugm_list)} members to user group {self.user_group_id}')

    def output_user_ids_str(self):
        u_ids = ';\n'.join(self.user_ids)
        print(f'User_ids for users in input file:\n\n{u_ids}')
        if sorted(self.added_user_ids) != sorted(self.user_ids):
            added_ids = ';\n'.join(self.added_user_ids)
            print(f'\n\n\nUser_ids for users added to user group {self.user_group_id}:\n\n{added_ids}')

    def main(self):
        self.set_or_create_user_group()
        self.populate_user_group()
        self.output_user_ids_str()


if __name__ == '__main__':
    manager = ImportManager()
    manager.main()
