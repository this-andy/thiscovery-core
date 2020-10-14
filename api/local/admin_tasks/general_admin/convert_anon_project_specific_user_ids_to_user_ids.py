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
This script parses a CSV file containing anon_project_specific_user_ids and outputs a CSV file of matching user_ids
"""

import csv
import os
from tkinter import Tk
from tkinter.filedialog import askopenfilename

import api.endpoints.user as u
import api.common.utilities as utils
from api.endpoints.user_group import UserGroup
from api.endpoints.user_group_membership import UserGroupMembership
from api.local.admin_tasks.admin_tasks_utilities import CsvImporter


class ImportManager(CsvImporter):

    def __init__(self, anon_project_specific_user_id_column='anon_project_specific_user_id', csvfile_path=None):
        self.user_group_id = None
        super().__init__(anon_project_specific_user_id_column, csvfile_path=csvfile_path)
        super().validate_input_file_and_get_users()


if __name__ == '__main__':
    manager = ImportManager()
    print(manager.output_csv_of_user_ids())
