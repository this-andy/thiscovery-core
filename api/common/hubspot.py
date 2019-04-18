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
from urllib.request import urlopen
import logging
import boto3
import sys
import datetime

# from .utilities import sqs_send


api_key = '274d0bed-3cf7-458f-a0b7-173ba154dca4'
# api_key = 'demo'
api_key_string = '?hapikey=' + api_key
base_url = 'https://api.hubapi.com'


def get_hubspot_contact(email):
    full_url = base_url + '/contacts/v1/contact/vid/5727886/profile' + api_key_string

    full_url = 'http://api.hubapi.com/contacts/v1/lists/all/contacts/all?count=2&hapikey=274d0bed-3cf7-458f-a0b7-173ba154dca4'
    # full_url = 'https://api.hubapi.com/contacts/v1/lists/all/contacts/all?count=2&hapikey=b6af5e7f-27c3-42bd-a18d-2273f3272a4a'
    response = urlopen(full_url).read()
    data = json.loads(response)
    return response


def update_contact(email):
    url = 'http://api.hubapi.com/contacts/v1/contact/email/' + email + '/profile' + api_key_string
    headers = {}
    headers['Content-Type'] = 'application/json'

    data = json.dumps({
        "properties": [
            {
                "property": "lastname",
                "value": "hello world!"
            },
        ]
    })

    r = requests.post(data=data, url=url, headers=headers)

    return r.status_code


def authorise():
    # Build the auth URL
    client_id = '1de8822d-d7da-4ed4-99bb-429f593e345c'
    scopes = 'contacts'
    redirect_url = 'www.thiscovery.org'
    authUrl = 'https://app.hubspot.com/oauth/authorize' + \
    '?client_id=' + client_id + \
    '&scope=' + scopes + \
    '&redirect_uri=' + redirect_url

    res = requests.post(authUrl)
    return res.status_code

if __name__ == "__main__":
    result = authorise()
    # result = get_hubspot_contact(None)
    # result = update_contact('coolrobot@hubspot.com')

    # message_body = (
    #         'Information about current NY Times fiction bestseller for '
    #         'week of 12/11/2016.'
    #     )
    # message_attributes = {
    #         'Title': {
    #             'DataType': 'String',
    #             'StringValue': 'The Whistler'
    #         },
    #         'Author': {
    #             'DataType': 'String',
    #             'StringValue': 'John Grisham'
    #         },
    #         'WeeksOn': {
    #             'DataType': 'Number',
    #             'StringValue': '6'
    #         }
    #     }
    # result = sqs_send(message_body, message_attributes)
    print(result)