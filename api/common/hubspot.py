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
import uuid
import requests
from urllib.request import urlopen
from api.common.utilities import get_secret, get_aws_region, get_logger
import logging
import boto3
import sys
import datetime

from api.endpoints.user import patch_user
# from ..endpoints.user import patch_user


hubspot_connection = get_secret('hubspot-connection')
api_key = hubspot_connection['api-key']
client_id = hubspot_connection['client-id']
client_secret = hubspot_connection['client-secret']
api_key_string = '?hapikey=' + api_key
base_url = 'http://api.hubapi.com'


def get_hubspot_contact(email):
    full_url = base_url + '/contacts/v1/lists/all/contacts/all' + api_key_string
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
    scopes = 'contacts'
    redirect_url = 'http://e1ac49d6.ngrok.io/hubspot'
    authUrl = 'https://app.hubspot.com/oauth/authorize' + \
    '?client_id=' + client_id + \
    '&scope=' + scopes + \
    '&redirect_uri=' + redirect_url

    res = requests.post(authUrl)
    return res.status_code


def get_token():
    redirect_url = 'https://www.hubspot.com/auth-callback'
    code = 'd7f2fa01-4988-44f3-98c6-d3aaef0f13f4'
    formData = {
        "grant_type": "authorization_code",
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_url,
        "code": code
    };

    res = requests.post('https://api.hubapi.com/oauth/v1/token', data=formData)
    return res.status_code


def post_new_user_to_crm(new_user):
    id = new_user['id']
    email = new_user['email']

    url =  base_url + '/contacts/v1/contact/createOrUpdate/email/' + email + api_key_string
    headers = {}
    headers['Content-Type'] = 'application/json'

    data = json.dumps({
        "properties": [
            {
                "property": "email",
                "value": email
            },
            {
                "property": "firstname",
                "value": new_user['first_name']
            },
            {
                "property": "lastname",
                "value": new_user['last_name']
            }
        ]
    })

    result = requests.post(data=data, url=url, headers=headers)

    if result.status_code == 200:
        pass
        content_str = result.content.decode('utf-8')
        content = json.loads(content_str)
        vid = content['vid']
        isNew = content['isNew']

        user_jsonpatch = [
            {'op': 'replace', 'path': '/crm_id', 'value': str(vid)},
        ]

        patch_user(id, user_jsonpatch)
        pass
    elif result.status_code == 400:
        pass
    else:
        pass

    return result.status_code
    pass


if __name__ == "__main__":
    result = get_token()
    # result = get_hubspot_contact(None)
    # result = update_contact('coolrobot@hubspot.com')

    # new_user = {
    #     "id": str(uuid.uuid4()),
    #     "created": "2018-08-21T11:16:56+01:00",
    #     "email": "dh@hubspot.com",
    #     "title": "Mr",
    #     "first_name": "David",
    #     "last_name": "Harris",
    #     "auth0_id": "1235abcd",
    #     "status": "new"
    #   }

    # result = post_new_user_to_crm(new_user)

    print(result)