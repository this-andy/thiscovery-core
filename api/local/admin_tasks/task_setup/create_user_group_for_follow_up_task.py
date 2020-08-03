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
This script parses a CSV file containing user identifiers and creates a user group in Thiscovery
"""

import csv
import os
from tkinter import Tk
from tkinter.filedialog import askopenfilename

import api.endpoints.user as u
import api.common.utilities as utils
from api.endpoints.user_group import UserGroup
from api.endpoints.user_group_membership import UserGroupMembership


class ImportManager:

    def __init__(self, anon_project_specific_user_id_column='anon_project_specific_user_id'):
        self.anon_project_specific_user_id_column = anon_project_specific_user_id_column
        self.input_filename = self.prompt_user_for_input_data()
        self.logger = utils.get_logger()
        self.user_ids = list()
        self.user_group_id = None

    def prompt_user_for_input_data(self):
        root = Tk()
        root.withdraw()  # we don't want a full GUI, so keep the root window from appearing
        filename = askopenfilename(
            initialdir=os.path.expanduser('~'),
            title="Please select input file",
            filetypes=(("csv files", "*.csv"), ("all files", "*.*"))
        )
        return filename

    def validate_input_file_and_get_user_ids(self):
        """
        Checks that input csv file has only one row per user and that users exist in thiscovery db
        """
        anon_ids_in_file = list()
        with open(self.input_filename) as csv_f:
            reader = csv.DictReader(csv_f)
            rows = list(reader)
            for i, row in enumerate(rows):
                print(f'Validating input file row {i+1} of {len(rows)}')
                anon_id = row[self.anon_project_specific_user_id_column]
                if anon_id in anon_ids_in_file:
                    raise ValueError(f'Input csv file has more than one row for user {anon_id}')
                    # pass
                else:
                    user_id = u.get_user_by_anon_project_specific_user_id(anon_id)[0]['id']
                    self.user_ids.append(user_id)
                    anon_ids_in_file.append(anon_id)

    def create_user_group(self):
        print(f'Found {len(self.user_ids)} users in input file. User ids are: {self.user_ids}')
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

    def populate_user_group(self):
        ugm_list = list()
        for user_id in self.user_ids:
            ugm_json = {
                'user_id': user_id,
                'user_group_id': self.user_group_id,
            }
            ugm = UserGroupMembership.from_json(ugm_json, None)
            ugm.insert_to_db()
            ugm_id = ugm.to_dict()['id']
            ugm_list.append(ugm_id)
        print(f'Added {len(ugm_list)} members to user group {self.user_group_id}')

    def main(self):
        self.prompt_user_for_input_data()
        self.validate_input_file_and_get_user_ids()
        self.create_user_group()
        self.populate_user_group()


if __name__ == '__main__':
    manager = ImportManager()
    manager.main()
