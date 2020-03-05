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

import json
import requests
from urllib.error import HTTPError
from http import HTTPStatus
from datetime import datetime

import common.dynamodb_utilities as ddb
from common.utilities import get_secret, get_logger, get_aws_namespace, DetailedValueError, now_with_tz

BASE_URL = 'https://cambridge.eu.qualtrics.com/API/'


def qualtrics_request(method, endpoint_url, api_key, base_url=BASE_URL, params=None, data=None):
    full_url = base_url + endpoint_url
    headers = {
        "content-type": "application/json",
        "Accept": "application/json",
        "x-api-token": api_key,
    }

    response = requests.request(
        method=method,
        url=full_url,
        params=params,
        headers=headers,
        data=data,
    )

    if response.ok:
        return response.json()
    else:
        raise DetailedValueError(f'Call to Qualtrics API failed with response: {response.content}')


def create_survey(survey_name):
    endpoint = "v3/survey-definitions"
    data = {
        "SurveyName": survey_name,
        "Language": "EN",
        "ProjectCategory": "CORE",
    }


response = requests.post(baseUrl, json=data, headers=headers)
print(response.text)