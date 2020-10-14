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
import csv
import os
from tkinter import Tk
from tkinter.filedialog import askopenfilename

import thiscovery_lib.utilities as utils
import api.endpoints.user as u


class CsvImporter:

    def __init__(self, anon_project_specific_user_id_column, csvfile_path=None):
        self.logger = utils.get_logger()
        self.anon_project_specific_user_id_column = anon_project_specific_user_id_column
        self.users = list()
        self.user_ids = list()
        self.anon_project_specific_user_ids = list()
        self.anon_id_to_user_id_map = dict()
        self.anon_id_to_user_map = dict()

        self.input_filename = csvfile_path
        if csvfile_path is None:
            root = Tk()
            root.withdraw()  # we don't want a full GUI, so keep the root window from appearing
            root.update()
            self.input_filename = askopenfilename(
                initialdir=os.path.expanduser('~'),
                title="Please select input file",
                filetypes=(("csv files", "*.csv"), ("all files", "*.*"))
            )
            root.update()
            root.destroy()

    def validate_input_file_and_get_users(self):
        """
        Checks that input csv file has only one row per user and that users exist in thiscovery db
        """
        with open(self.input_filename) as csv_f:
            reader = csv.DictReader(csv_f)
            rows = list(reader)
            for i, row in enumerate(rows):
                print(f'Validating input file row {i+1} of {len(rows)}')
                anon_id = row[self.anon_project_specific_user_id_column]

                if not anon_id:
                    self.logger.warning('Missing value in anon_project_specific_user_id column; skipped row', extra={'row': row})
                    continue
                elif anon_id == 'anon_project_specific_user_id':
                    self.logger.warning('Skipped row of putative Qualtrics labels', extra={'row': row})
                    continue

                if anon_id in self.anon_project_specific_user_ids:
                    raise ValueError(f'Input csv file has more than one row for user {anon_id}')
                else:
                    user = u.get_user_by_anon_project_specific_user_id(anon_id)[0]
                    user_id = user['id']
                    if user:
                        self.users.append(user)
                        self.user_ids.append(user_id)
                        self.anon_project_specific_user_ids.append(anon_id)
                        self.anon_id_to_user_id_map[anon_id] = user_id
                        self.anon_id_to_user_map[anon_id] = user
                    else:
                        raise ValueError(f'User {anon_id} could not be found')

    def output_csv_of_user_ids(self):
        root, ext = os.path.splitext(self.input_filename)
        output_filename = f"{root}_user_ids{ext}"
        with open(output_filename, 'w') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([self.anon_project_specific_user_id_column, 'user_id'])
            for k, v in self.anon_id_to_user_id_map.items():
                writer.writerow([k, v])

    def output_csv_of_user_info(self):
        root, ext = os.path.splitext(self.input_filename)
        output_filename = f"{root}_user_info{ext}"
        with open(output_filename, 'w') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow([self.anon_project_specific_user_id_column, *list(self.users[0].keys())])
            for k, v in self.anon_id_to_user_map.items():
                writer.writerow([k, *list(v.values())])
