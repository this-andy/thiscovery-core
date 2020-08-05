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
import http
import os
import pandas as pd
from tkinter import Tk
from tkinter.filedialog import askopenfilename

import api.endpoints.project as p
import api.endpoints.user as u
import api.common.utilities as utils
from api.common.dynamodb_utilities import Dynamodb
from api.local.admin_tasks.admin_tasks_utilities import CsvImporter


class ProcessManager(CsvImporter):

    def __init__(self, anon_project_specific_user_id_column='anon_project_specific_user_id'):
        self.anon_project_specific_user_id_column = anon_project_specific_user_id_column
        super().__init__(anon_project_specific_user_id_column)

    def transform(self):
        df = pd.read_csv(self.input_filename)

        # Delete redundant row (column labels) from Qualtrics results
        if df.at[0, 'StartDate'] == 'Start Date':
            df.drop(index=0, inplace=True)

        df.RecipientEmail = 'no.email@thisinstitute.cam.ac.uk'
        df.ExternalReference = df.anon_project_specific_user_id
        # Keep only rows where anon_project_specific_user_id is not null (based on https://stackoverflow.com/a/18173074)
        df = df[pd.notna(df.anon_project_specific_user_id) == True]

        df.drop(inplace=True, columns=[
            'StartDate',
            'EndDate',
            'Status',
            'IPAddress',
            'Progress',
            'Duration (in seconds)',
            'Finished',
            'RecordedDate',
            'ResponseId',
            'LocationLatitude',
            'LocationLongitude',
            'DistributionChannel',
            'UserLanguage',
            'anon_user_task_id',
        ])

        df.rename(inplace=True, columns={
            'RecipientLastName': 'LastName',
            'RecipientFirstName': 'FirstName',
            'RecipientEmail': 'PrimaryEmail',
            'ExternalReference': 'ExternalDataReference',
        })

        df.to_csv(f'Contact_data_based_on_{os.path.basename(self.input_filename).replace("_", "-")}', index=False)


if __name__ == '__main__':
    manager = ProcessManager()
    manager.transform()
