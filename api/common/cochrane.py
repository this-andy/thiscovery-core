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

import requests

import common.utilities as utils


def cochrane_get(url):
    full_url = utils.get_secret('cochrane-connection')['base_url'] + url
    headers = dict()
    headers['Content-Type'] = 'application/json'
    logger = utils.get_logger()
    response = requests.get(full_url, headers=headers)
    if response.ok:
        data = response.json()
        logger.info('API response', extra={'body': data})
        return data
    else:
        raise utils.DetailedValueError('Cochrane API call failed', details={'response': response.content})


def get_progress(url='/CrowdService/v1/this/progress'):
    return cochrane_get(url)
