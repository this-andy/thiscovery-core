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

import common.utilities as utils

from api.local.secrets import QUALTRICS_API_TOKEN


class BaseClient:

    def __init__(self, api_token=QUALTRICS_API_TOKEN):
        self.base_url = 'https://cambridge.eu.qualtrics.com/API'
        self.api_token = api_token
        self.logger = utils.get_logger()

    def qualtrics_request(self, method, endpoint_url, api_key=None, params=None, data=None):
        if api_key is None:
            api_key = self.api_token

        headers = {
            "content-type": "application/json",
            "Accept": "application/json",
            "x-api-token": api_key,
        }

        self.logger.debug('Qualtrics API call', extra={'method': method, 'url': endpoint_url, 'params': params, 'json': data})
        response = requests.request(
            method=method,
            url=endpoint_url,
            params=params,
            headers=headers,
            json=data,
        )

        if response.ok:
            return response.json()
        else:
            print(response.text)
            raise utils.DetailedValueError('Call to Qualtrics API failed', details={'response.text': response.text})


class SurveyDefinitionsClient(BaseClient):

    def __init__(self, survey_id):
        super().__init__()
        self.base_endpoint = f"{self.base_url}/v3/survey-definitions/{survey_id}"
        self.questions_endpoint = f"{self.base_endpoint}/questions"
        self.blocks_endpoint = f"{self.base_endpoint}/blocks"

    def get_survey(self):
        return self.qualtrics_request("GET", self.base_endpoint)

    def create_question(self, data):
        return self.qualtrics_request("POST", self.questions_endpoint, data=data)

    def update_question(self, question_id, data):
        endpoint = f"{self.questions_endpoint}/{question_id}"
        return self.qualtrics_request("PUT", endpoint, data=data)

    def delete_question(self, question_id):
        endpoint = f"{self.questions_endpoint}/{question_id}"
        return self.qualtrics_request("DELETE", endpoint)
    
    def create_block(self, data):
        return self.qualtrics_request("POST", self.blocks_endpoint, data=data)

    def update_block(self, block_id, data):
        endpoint = f"{self.blocks_endpoint}/{block_id}"
        return self.qualtrics_request("PUT", endpoint, data=data)

    def delete_block(self, block_id):
        endpoint = f"{self.blocks_endpoint}/{block_id}"
        return self.qualtrics_request("DELETE", endpoint)
