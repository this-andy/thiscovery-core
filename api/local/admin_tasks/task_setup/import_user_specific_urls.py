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
This script reads user-specific user task urls (and additional data) from an input csv file
and stores the values in a UserSpecificUrls Dynamodb table.
"""

import csv
import http
import os
from tkinter import Tk
from tkinter.filedialog import askopenfilename

import api.endpoints.project as p
import api.endpoints.user as u
import api.common.utilities as utils
from api.common.dynamodb_utilities import Dynamodb
from api.local.admin_tasks.admin_tasks_utilities import CsvImporter


class ImportManager(CsvImporter):

    def __init__(self, anon_project_specific_user_id_column='External Data Reference'):
        self.anon_project_specific_user_id_column = anon_project_specific_user_id_column
        self.ddb = Dynamodb()
        self.project_task_id = input("Please enter the project task id:")
        super().__init__()

    def check_project_task_exists(self):
        if not p.get_project_task(self.project_task_id):
            raise utils.ObjectDoesNotExistError(f'Project task {self.project_task_id} could not be found')

    def nullify_empty_attributes(self, row):
        """
        This is required because ddb does not accept empty strings as attribute values
        """
        for k, v in row.items():
            if v == "":
                row[k] = None
        return row

    def populate_ddb(self):
        with open(self.input_filename) as csv_f:
            reader = csv.DictReader(csv_f)
            rows = list(reader)
            for i, row in enumerate(rows):
                print(f'Populating Dynamodb with row {i+1} of {len(rows)}')
                anon_id = row[self.anon_project_specific_user_id_column]
                users = u.get_user_by_anon_project_specific_user_id(anon_id)
                user = users[0]
                user_id = user['id']
                user_specific_url = row['Link']
                key = f"{self.project_task_id}_{user_id}"
                details = self.nullify_empty_attributes(row)
                response = self.ddb.put_item(
                    table_name='UserSpecificUrls',
                    key=key,
                    item_type='user_specific_url',
                    item_details=details,
                    item={
                        'user_id': user_id,
                        'anon_project_specific_user_id': anon_id,
                        'project_task_id': self.project_task_id,
                        'user_specific_url': user_specific_url,
                        'details_provenance': os.path.basename(self.input_filename),
                        'status': 'new',
                    },
                    update_allowed=True,
                )
                assert response['ResponseMetadata']['HTTPStatusCode'] == http.HTTPStatus.OK, f"DynamoDb raised an error. Here is the response: {response}"

    def main(self):
        self.check_project_task_exists()
        super().validate_input_file_and_get_user_ids()
        self.populate_ddb()


if __name__ == '__main__':
    manager = ImportManager()
    manager.main()
