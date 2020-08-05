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

import api.common.utilities as utils
import api.endpoints.user as u


class CsvImporter:

    def __init__(self, anon_project_specific_user_id_column):
        self.logger = utils.get_logger()
        self.user_ids = list()
        self.anon_project_specific_user_id_column = anon_project_specific_user_id_column

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
                else:
                    user_id = u.get_user_by_anon_project_specific_user_id(anon_id)[0]['id']
                    if user_id:
                        self.user_ids.append(user_id)
                        anon_ids_in_file.append(anon_id)
                    else:
                        raise ValueError(f'User {anon_id} could not be found')
