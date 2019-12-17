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
import uuid
from urllib.request import urlopen, Request, HTTPError
from http import HTTPStatus
from datetime import datetime

BASE_URL_PRODUCTION = 'https://crs.cochrane.org'
BASE_URL_STAGING = 'https://api-test.metaxis.com'
BASE_URL_MOCK_API = 'https://720c06c1-663e-4fd9-bcf9-63bf5d933779.mock.pstmn.io'

base_url = BASE_URL_MOCK_API
# base_url = BASE_URL_PRODUCTION


def cochrane_get(url):
    full_url = base_url + url
    headers = dict()
    headers['Content-Type'] = 'application/json'
    try:
        req = Request(full_url, headers=headers)
        response = urlopen(req).read()
        data = json.loads(response)
    except HTTPError as err:
        if err.code == HTTPStatus.NOT_FOUND:
            return None
        else:
            raise err
    return data


def get_progress():
    url = '/CrowdService/v1/this/progress'
    return cochrane_get(url)


if __name__ == '__main__':
    # print(get_progress())
    pass
