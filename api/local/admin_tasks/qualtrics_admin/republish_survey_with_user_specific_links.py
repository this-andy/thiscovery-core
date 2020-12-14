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
This script generates individual distribution links for a pre-existing survey and contact list (aka mailing list) in Qualtrics,
and exports those links to Dynamodb

Usage: Run this file after setting the values of SURVEY_ID, CONTACT_LIST_ID and PROJECT_TASK_ID
"""

import os

import thiscovery_lib.qualtrics as qualtrics
import api.endpoints.user_task as ut

from thiscovery_lib.dynamodb_utilities import Dynamodb
from api.local.admin_tasks.task_management.import_user_specific_urls import ImportManager


class DistributionLinksGenerator:

    def __init__(self, survey_id, contact_list_id, project_task_id):
        self.survey_id = survey_id
        self.contact_list_id = contact_list_id
        self.dist_client = qualtrics.DistributionsClient()
        self.ddb_client = Dynamodb()
        self.project_task_id = project_task_id
        ImportManager.check_project_task_exists(self.project_task_id)

    def generate_links_and_upload_to_dynamodb(self):
        r = self.dist_client.create_individual_links(survey_id=self.survey_id, contact_list_id=self.contact_list_id)
        distribution_id = r['result']['id']
        r = self.dist_client.list_distribution_links(distribution_id, self.survey_id)
        rows = r['result']['elements']
        for row in rows:
            ImportManager.import_row(
                row_dict=row,
                anon_project_specific_user_id_column='externalDataReference',
                link_column='link',
                project_task_id=self.project_task_id,
                provenance={
                    'survey_id': self.survey_id,
                    'distribution_id': distribution_id,
                    'contact_id': row.get('contactId'),
                    'process': os.path.basename(__file__),
                },
                dynamodb_client=self.ddb_client,
            )


if __name__ == '__main__':
    SURVEY_ID = None
    CONTACT_LIST_ID = None
    PROJECT_TASK_ID = None
    for param in [SURVEY_ID, CONTACT_LIST_ID, PROJECT_TASK_ID]:
        if param is None:
            raise ValueError('Please set the values of SURVEY_ID, CONTACT_LIST_ID and PROJECT_TASK_ID before running this script')
    link_generator = DistributionLinksGenerator(survey_id=SURVEY_ID, contact_list_id=CONTACT_LIST_ID, project_task_id=PROJECT_TASK_ID)
    link_generator.generate_links_and_upload_to_dynamodb()
    ut.clear_user_tasks_for_project_task_id(PROJECT_TASK_ID)
