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
This script generates individual distribution links for an pre-existing contact list (aka mailing list) in Qualtrics

https://api.qualtrics.com/api-reference/reference/distributions.json/paths/~1distributions/post
"""

import csv
import os
import sys
from pprint import pprint
from tkinter import Tk
from tkinter.filedialog import askopenfilename

import api.common.pg_utilities as pg_utils
import api.common.sql_queries as sql_q
import api.common.utilities as utils

from api.common.dev_config import SECRETS_NAMESPACE


class DistributionLinksGenerator:

    def __init__(self, survey_id, contact_list_id):
        self.survey_id = survey_id
        self.contact_list_id = contact_list_id

    def generate_links(self):
        pass


if __name__ == '__main__':
    SURVEY_ID = 'SV_aYlEogmXyMAINOB'
    CONTACT_LIST_ID = 'ML_098uUdQjO4oI9h3'
    link_generator = DistributionLinksGenerator(survey_id=SURVEY_ID, contact_list_id=CONTACT_LIST_ID)

