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
from urllib.request import urlopen, Request, HTTPError
from http import HTTPStatus
from datetime import datetime
import uuid

from api.common.utilities import get_secret, get_logger, now_with_tz
from api.common.dynamodb_utilities import get_item, put_item

# from .utilities import get_secret, get_logger, now_with_tz
# from .dynamodb_utilities import get_item, put_item

ISO_DATE_FORMAT = '%Y-%m-%d %H:%M:%S.%f%z'

logger = get_logger()
# use namespace_override to enable using dev hubspot with production Thiscovery
hubspot_connection = get_secret('hubspot-connection', namespace_override='/dev/')
logger.info('hubspot_connection:' + str(hubspot_connection))

print ('hubspot-connection' + str(hubspot_connection))
client_id = hubspot_connection['client-id']
client_secret = hubspot_connection['client-secret']
base_url = 'http://api.hubapi.com'


# region Contact property and group management

def create_property1(property_definition):
    url = '/properties/v1/contacts/properties'

    data = {
        "name": "thiscovery_id",
        "label": "Thiscovery ID",
        "description": "Contact's unique user ID in Thiscovery API",
        "groupName": "thiscovery",
        "type": "string",
        "fieldType": "text",
        "formField": False
    }

    r = hubspot_post(url, data)

    return r.status_code

def create_property2(property_definition):
    url = '/properties/v1/contacts/properties'

    data = {
        "name": "thiscovery_registered_date",
        "label": "Registered on Thiscovery date",
        "description": "The date on which a person first registered on Thiscovery.  Automatically set when someone registers.",
        "groupName": "thiscovery",
        "type": "datetime",
        "fieldType": "text",
        "formField": False
    }

    r = hubspot_post(url, data)

    return r.status_code


def update_property(property_definition):
    url = '/properties/v1/contacts/properties/named/newapicustomproperty4'

    data = json.dumps({
        "name": "newapicustomproperty4",
        "label": "Api Custom Property4",
        "description": "A new property for you",
        "groupName": "contactinformation",
        "type": "datetime",
        "fieldType": "text",
        "formField": False,
        "displayOrder": 6,
        "readOnlyValue": True
    })

    r = hubspot_put(url, data)

    return r.status_code


def create_group(group_definition):
    url = '/properties/v1/contacts/groups'

    data = {
        "name": "thiscovery",
        "displayName": "Thiscovery"
    }

    r = hubspot_post(url, data)

    return r.status_code
# endregion

# region core hubspot crud methods

def hubspot_get(url):
    success = False
    retry_count = 0
    full_url = base_url + url
    headers = {}
    headers['Content-Type'] = 'application/json'
    while not success:
        try:
            headers['Authorization'] = 'Bearer ' + get_current_access_token()
            req = Request(full_url, headers=headers)
            response = urlopen(req).read()
            data = json.loads(response)
            success = True
        except HTTPError as err:
            if err.code == HTTPStatus.UNAUTHORIZED and retry_count <= 1:
                refresh_token()
                retry_count += 1
                # and loop to retry
            else:
                raise err
    return data


def hubspot_post(url: str, data: dict):
    success = False
    retry_count = 0
    full_url = base_url + url
    headers = {}
    headers['Content-Type'] = 'application/json'
    while not success:
        try:
            headers['Authorization'] = 'Bearer ' + get_current_access_token()

            result = requests.post(data=json.dumps(data), url=full_url, headers=headers)
            if result.status_code in [HTTPStatus.OK, HTTPStatus.NO_CONTENT, HTTPStatus.CREATED]:
                success = True
            elif result.status_code == HTTPStatus.UNAUTHORIZED and retry_count <= 1:
                refresh_token()
                retry_count += 1
                # and loop to retry
            else:
                raise err
        except HTTPError as err:
            if err.code == HTTPStatus.UNAUTHORIZED and retry_count <= 1:
                refresh_token()
                retry_count += 1
                # and loop to retry
            else:
                raise err

    return result


def hubspot_put(url, data):
    success = False
    retry_count = 0
    full_url = base_url + url
    headers = {}
    headers['Content-Type'] = 'application/json'
    while not success:
        try:
            headers['Authorization'] = 'Bearer ' + get_current_access_token()

            result = requests.put(data=data, url=full_url, headers=headers)
            if result.status_code in [HTTPStatus.OK, HTTPStatus.NO_CONTENT, HTTPStatus.CREATED]:
                success = True
            elif result.status_code == HTTPStatus.UNAUTHORIZED and retry_count <= 1:
                refresh_token()
                retry_count += 1
                # and loop to retry
            else:
                raise err
        except HTTPError as err:
            if err.code == HTTPStatus.UNAUTHORIZED and retry_count <= 1:
                refresh_token()
                retry_count += 1
                # and loop to retry
            else:
                raise err

    return result

# endregion


def get_hubspot_contact():
    url = '/contacts/v1/lists/all/contacts/all'
    return hubspot_get(url)


def update_contact(email: str, property_changes: list):
    url = '/contacts/v1/contact/email/' + email + '/profile'

    data = {"properties": property_changes}

    r = hubspot_post(url, data)

    return r.status_code


# region token processing

def get_token_from_database() -> dict:
    try:
        token = get_item('tokens', 'hubspot')['details']
    except:
        token = None
    return token


hubspot_oauth_token = None


def save_token(new_token):
    put_item('tokens', 'oAuth_token', new_token, {}, 'hubspot')


def get_current_access_token() -> str:
    global hubspot_oauth_token
    if hubspot_oauth_token is None:
        hubspot_oauth_token = get_token_from_database()
    return hubspot_oauth_token['access_token']


def get_new_token_from_hubspot(refresh_token, code=None):
    global hubspot_oauth_token
    redirect_url = 'https://www.hubspot.com/auth-callback'
    formData = {
        "client_id": client_id,
        "client_secret": client_secret,
        "redirect_uri": redirect_url,
    }

    if refresh_token:
        formData['grant_type'] = "refresh_token"
        formData['refresh_token'] = refresh_token
    else:
        formData['grant_type'] = "authorization_code"
        formData['code'] = code

    res = requests.post('https://api.hubapi.com/oauth/v1/token', data=formData)
    token_text = res.text
    token = json.loads(token_text)
    save_token(token)
    hubspot_oauth_token = token
    return token


def refresh_token():
    refresh_token = hubspot_oauth_token['refresh_token']
    return get_new_token_from_hubspot(refresh_token)


def get_initial_token_from_hubspot():
    code = "ef5a69d0-4578-4fa8-8137-abf691d691a4"   # paste this from thiscovery admin
    return get_new_token_from_hubspot(None, code)

hubspot_oauth_token = get_token_from_database()

# endregion


def post_new_user_to_crm(new_user):
    email = new_user['email']

    url = '/contacts/v1/contact/createOrUpdate/email/' + email

    created_time = datetime.strptime(new_user['created'], ISO_DATE_FORMAT)
    created_timestamp = int(created_time.timestamp() * 1000)

    data = {
        "properties": [
            {"property": "email", "value": email},
            {"property": "firstname", "value": new_user['first_name']},
            {"property": "lastname", "value": new_user['last_name']},
            {"property": "thiscovery_id", "value": new_user['id']},
            {"property": "thiscovery_registered_date", "value": created_timestamp},
            {"property": "country", "value": new_user['country_name']},
        ]
    }

    result = hubspot_post(url, data)

    if result.status_code == HTTPStatus.OK:

        content_str = result.content.decode('utf-8')
        content = json.loads(content_str)
        vid = content['vid']
        is_new = content['isNew']
        return vid, is_new

    else:
        return -1, False


# def post_task_signup_to_crm(task_signup):
#
#     url =  '/contacts/v1/contact/createOrUpdate/email/'
#
#     data = {
#         "properties": [
#             {
#                 "property": "firstname",
#                 "value": task_signup['first_name']
#             },
#             {
#                 "property": "lastname",
#                 "value": task_signup['last_name']
#             },
#         ]
#     }
#
#     return hubspot_post(url, data)


if __name__ == "__main__":
    pass

    # result = create_group(None)

    result = create_property1(None)
    # result = update_property(None)

    # result = get_initial_token_from_hubspot()
    # token = get_token_from_database()
    # result = get_new_token_from_hubspot(token['refresh_token'])
    # result = get_hubspot_contact()

    # n = now_with_tz()
    # tsn = n.timestamp() * 1000
    # changes = [
    #         {"property": "thiscovery_registered_date", "value": int(tsn)},
    #     ]
    # result = update_contact('aw@email.co.uk', changes)

    # new_user = {
    #     "id": str(uuid.uuid4()),
    #     "created": "2018-08-21T11:16:56+01:00",
    #     "email": "eh@hubspot.com",
    #     "title": "Ms",
    #     "first_name": "Erica",
    #     "last_name": "Harris",
    #     "auth0_id": "1235abcd",
    #     "status": "new"
    #   }
    #
    # result = post_new_user_to_crm(new_user)

    # result = get_token_from_database()
    print(result)

    # save_token(result_2019_05_10_12_11)