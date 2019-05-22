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

# from api.common.utilities import get_secret, get_logger, now_with_tz, DetailedValueError
# from api.common.dynamodb_utilities import get_item, put_item

from .utilities import get_secret, get_logger, now_with_tz
from .dynamodb_utilities import get_item, put_item

DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# use namespace_override to enable using dev hubspot with production Thiscovery
# hubspot_connection = get_secret('hubspot-connection', namespace_override='/dev/')
#
# client_id = hubspot_connection['client-id']
# client_secret = hubspot_connection['client-secret']

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

    data = {
        "name": "newapicustomproperty4",
        "label": "Api Custom Property4",
        "description": "A new property for you",
        "groupName": "contactinformation",
        "type": "datetime",
        "fieldType": "text",
        "formField": False,
        "displayOrder": 6,
        "readOnlyValue": True
    }

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

# region Timeline Events

def create_timeline_event(event_data: dict):
    hubspot_connection = get_secret('hubspot-connection')
    app_id = hubspot_connection['app-id']
    url = '/integrations/v1/' + app_id + '/timeline/event'

    result = hubspot_put(url, event_data)

    return result.status_code


def create_timeline_event_type(type_defn: dict):
    hubspot_connection = get_secret('hubspot-connection')
    app_id = hubspot_connection['app-id']
    type_defn['applicationId'] = app_id
    url = '/integrations/v1/' + app_id + '/timeline/event-types'

    response = hubspot_post(url, type_defn)
    content = json.loads(response.content)

    return content['id']


def delete_timeline_event_type(tle_type_id):
    hubspot_connection = get_secret('hubspot-connection')
    app_id = hubspot_connection['app-id']
    url = '/integrations/v1/' + app_id + '/timeline/event-types/' + str(tle_type_id)

    result = hubspot_delete(url)

    return result.status_code


def get_timeline_event_properties(tle_type_id):
    hubspot_connection = get_secret('hubspot-connection')
    app_id = hubspot_connection['app-id']
    url = '/integrations/v1/' + app_id + '/timeline/event-types/' + str(tle_type_id) + '/properties'

    result = hubspot_get(url)

    return result


def create_timeline_event_properties(tle_type_id, property_defns: list):
    hubspot_connection = get_secret('hubspot-connection')
    app_id = hubspot_connection['app-id']
    url = '/integrations/v1/' + app_id + '/timeline/event-types/' + str(tle_type_id) + '/properties'

    for property_defn in property_defns:
        result = hubspot_post(url, property_defn)

    return result.status_code


def delete_timeline_event_property(tle_type_id, property_id):
    hubspot_connection = get_secret('hubspot-connection')
    app_id = hubspot_connection['app-id']
    url = '/integrations/v1/' + app_id + '/timeline/event-types/' + str(tle_type_id) + '/properties/' + str(property_id)

    result = hubspot_delete(url)

    return result.status_code


# endregion

def create_TLE_for_task_signup():
    type_defn = {
            "name": "Task sign-up",
            "objectType": "CONTACT",
            "headerTemplate": "sample header template",
            "detailTemplate": "sample detail template"
        }

    TLE_type_id = create_timeline_event_type(type_defn)

    properties = [
        {
            "name": "project_id",
            "label": "Project Id",
            "propertyType": "String"
        },
        {
            "name": "project_name",
            "label": "Project Name",
            "propertyType": "String"
        },
        {
            "name": "task_id",
            "label": "Task Id",
            "propertyType": "String"
        },
        {
            "name": "task_name",
            "label": "Task Name",
            "propertyType": "String"
        },
        {
            "name": "task_type_id",
            "label": "Task Type Id",
            "propertyType": "String"
        },
        {
            "name": "task_type_name",
            "label": "Task Type",
            "propertyType": "String"
        },
        {
            "name": "signup_event_type",
            "label": "Event Type",
            "propertyType": "String"
        },
    ]

    result = create_timeline_event_properties(TLE_type_id, properties)


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
                raise Exception
        except HTTPError as err:
            if err.code == HTTPStatus.UNAUTHORIZED and retry_count <= 1:
                refresh_token()
                retry_count += 1
                # and loop to retry
            else:
                raise err


    return result


def hubspot_put(url: str, data: dict):
    success = False
    retry_count = 0
    full_url = base_url + url
    headers = {}
    headers['Content-Type'] = 'application/json'
    while not success:
        try:
            headers['Authorization'] = 'Bearer ' + get_current_access_token()

            result = requests.put(data=json.dumps(data), url=full_url, headers=headers)
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


def hubspot_delete(url):
    success = False
    retry_count = 0
    full_url = base_url + url
    headers = {}
    headers['Content-Type'] = 'application/json'
    while not success:
        try:
            headers['Authorization'] = 'Bearer ' + get_current_access_token()

            response = requests.delete(url=full_url, headers=headers)
            if response.status_code in [HTTPStatus.OK, HTTPStatus.NO_CONTENT]:
                success = True
            elif response.status_code == HTTPStatus.UNAUTHORIZED and retry_count <= 1:
                refresh_token()
                retry_count += 1
                # and loop to retry
            else:
                errorjson = {'url': url}
                content = json.loads(response.content)
                if 'message' in content:
                    msg = content['message']
                else:
                    msg = str(response.status_code)

                raise DetailedValueError(msg, errorjson)
        except HTTPError as err:
            if err.code == HTTPStatus.UNAUTHORIZED and retry_count <= 1:
                refresh_token()
                retry_count += 1
                # and loop to retry
            else:
                raise err

    return response

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
    put_item('tokens', 'oAuth_token', new_token, {}, 'hubspot', True)


def get_current_access_token() -> str:
    global hubspot_oauth_token
    if hubspot_oauth_token is None:
        hubspot_oauth_token = get_token_from_database()
    return hubspot_oauth_token['access_token']


def get_new_token_from_hubspot(refresh_token, code=None):
    global hubspot_oauth_token
    hubspot_connection = get_secret('hubspot-connection')
    client_id = hubspot_connection['client-id']
    client_secret = hubspot_connection['client-secret']

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
    code = "c841b8c9-930c-4967-8387-2fbdad393cb0"   # paste this from thiscovery admin
    return get_new_token_from_hubspot(None, code)

hubspot_oauth_token = get_token_from_database()

# endregion


def post_new_user_to_crm(new_user):
    email = new_user['email']

    url = '/contacts/v1/contact/createOrUpdate/email/' + email

    created_time_string = new_user['created'][:19] # strip milliseconds and timezone
    created_time = datetime.strptime(created_time_string, DATE_FORMAT)
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

    # result = create_property1(None)
    # result = update_property(None)

    # result = get_initial_token_from_hubspot()
    # result = get_token_from_database()
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

    type_defn = {
            "name": "Task sign-up",
            "objectType": "CONTACT",
            "headerTemplate": "sample header template",
            "detailTemplate": "sample detail template"
        }

    # result = create_timeline_event_type(type_defn)

    data = [
        {
            "name": "project_id",
            "label": "Project Id",
            "propertyType": "String"
        },
        {
            "name": "project_name",
            "label": "Project Name",
            "propertyType": "String"
        },
        {
            "name": "task_id",
            "label": "Task Id",
            "propertyType": "String"
        },
        {
            "name": "task_name",
            "label": "Task Name",
            "propertyType": "String"
        },
        {
            "name": "task_type_id",
            "label": "Task Type Id",
            "propertyType": "String"
        },
        {
            "name": "task_type_name",
            "label": "Task Type",
            "propertyType": "String"
        },
        {
            "name": "signup_event_type",
            "label": "Event Type",
            "propertyType": "String"
        },
    ]

    # result = create_timeline_event_properties('279633', data)

    # result = delete_timeline_event_property('279633', '480994')

    # result = get_timeline_event_properties ('279633')

    event_data = {
        "id": str(uuid.uuid4()),
        "objectId": 1101,
        "eventTypeId": "279633",
        "study-name": "Test 6 from API with date",
    }

    # result = create_timeline_event(event_data)

    # result = delete_timeline_event_type(390519)

    result = create_TLE_for_task_signup()

    print(result)

    # save_token(result_2019_05_10_12_11)