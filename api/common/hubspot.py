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

if __name__ == "__main__":
    from api.common.utilities import get_secret, get_logger, get_aws_namespace, DetailedValueError
    from api.common.dynamodb_utilities import get_item, put_item
else:
    from .utilities import get_secret, get_logger, get_aws_namespace, DetailedValueError
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

    r = hubspot_post(url, data, None)

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

    r = hubspot_post(url, data, None)

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

    r = hubspot_put(url, data, None)

    return r.status_code


def create_group(group_definition):
    url = '/properties/v1/contacts/groups'

    data = {
        "name": "thiscovery",
        "displayName": "Thiscovery"
    }

    r = hubspot_post(url, data, None)

    return r.status_code

# endregion

# region Timeline Events

def create_or_update_timeline_event(event_data: dict, correlation_id):
    hubspot_connection = get_secret('hubspot-connection')
    app_id = hubspot_connection['app-id']
    url = '/integrations/v1/' + app_id + '/timeline/event'

    result = hubspot_put(url, event_data, correlation_id)

    return result.status_code


def create_timeline_event_type(type_defn: dict):
    hubspot_connection = get_secret('hubspot-connection')
    app_id = hubspot_connection['app-id']
    type_defn['applicationId'] = app_id
    url = '/integrations/v1/' + app_id + '/timeline/event-types'

    response = hubspot_post(url, type_defn, None)
    content = json.loads(response.content)

    return content['id']


def delete_timeline_event_type(tle_type_id):
    hubspot_connection = get_secret('hubspot-connection')
    app_id = hubspot_connection['app-id']
    url = '/integrations/v1/' + app_id + '/timeline/event-types/' + str(tle_type_id)

    result = hubspot_delete(url, None)

    return result.status_code


def get_timeline_event_properties(tle_type_id):
    hubspot_connection = get_secret('hubspot-connection')
    app_id = hubspot_connection['app-id']
    url = '/integrations/v1/' + app_id + '/timeline/event-types/' + str(tle_type_id) + '/properties'

    result = hubspot_get(url, None)

    return result


def create_timeline_event_properties(tle_type_id, property_defns: list):
    hubspot_connection = get_secret('hubspot-connection')
    app_id = hubspot_connection['app-id']
    url = '/integrations/v1/' + app_id + '/timeline/event-types/' + str(tle_type_id) + '/properties'

    for property_defn in property_defns:
        result = hubspot_post(url, property_defn, None)


def delete_timeline_event_property(tle_type_id, property_id):
    hubspot_connection = get_secret('hubspot-connection')
    app_id = hubspot_connection['app-id']
    url = '/integrations/v1/' + app_id + '/timeline/event-types/' + str(tle_type_id) + '/properties/' + str(property_id)

    result = hubspot_delete(url, None)

    return result.status_code


# endregion

TASK_SIGNUP_TLE_TYPE_NAME = 'task-signup'


def create_TLE_for_task_signup():

    type_defn = {
            "name": TASK_SIGNUP_TLE_TYPE_NAME,
            "objectType": "CONTACT",
            "headerTemplate": "{{signup_event_type}} for {{task_name}}",
            "detailTemplate": "Project: {{project_name}}  {{project_id}}\nTask type: {{task_type_name}}  {{task_type_id}}"
        }

    tle_type_id = create_timeline_event_type(type_defn)

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

    result = create_timeline_event_properties(tle_type_id, properties)

    save_TLE_type_id(TASK_SIGNUP_TLE_TYPE_NAME, tle_type_id, None)


def save_TLE_type_id(name: str, hubspot_id, correlation_id):
    table_id = get_aws_namespace() + name
    details = {
        'hubspot_id': str(hubspot_id),
        'name': str(name),
    }
    put_item('lookups', table_id, 'tle_type', details, {}, True, correlation_id)


def get_TLE_type_id(name: str, correlation_id):
    table_id = get_aws_namespace() + name
    item = get_item('lookups', table_id, correlation_id)

    return item['details']['hubspot_id']


# region core hubspot crud methods

def hubspot_get(url, correlation_id):
    success = False
    retry_count = 0
    full_url = base_url + url
    headers = {}
    headers['Content-Type'] = 'application/json'
    while not success:
        try:
            headers['Authorization'] = 'Bearer ' + get_current_access_token(correlation_id)
            req = Request(full_url, headers=headers)
            response = urlopen(req).read()
            data = json.loads(response)
            success = True
        except HTTPError as err:
            if err.code == HTTPStatus.UNAUTHORIZED and retry_count <= 1:
                refresh_token(correlation_id)
                retry_count += 1
                # and loop to retry
            else:
                raise err
    return data


def hubspot_post(url: str, data: dict, correlation_id):
    success = False
    retry_count = 0
    full_url = base_url + url
    headers = {}
    headers['Content-Type'] = 'application/json'
    while not success:
        try:
            headers['Authorization'] = 'Bearer ' + get_current_access_token(correlation_id)

            result = requests.post(data=json.dumps(data), url=full_url, headers=headers)
            if result.status_code in [HTTPStatus.OK, HTTPStatus.NO_CONTENT, HTTPStatus.CREATED]:
                success = True
            elif result.status_code == HTTPStatus.UNAUTHORIZED and retry_count <= 1:
                refresh_token(correlation_id)
                retry_count += 1
                # and loop to retry
            else:
                errorjson = {'result': result}
                raise DetailedValueError('HTTP code ' + str(result.status_code), errorjson)
        except HTTPError as err:
            if err.code == HTTPStatus.UNAUTHORIZED and retry_count <= 1:
                refresh_token(correlation_id)
                retry_count += 1
                # and loop to retry
            else:
                raise err

    return result


def hubspot_put(url: str, data: dict, correlation_id):
    success = False
    retry_count = 0
    full_url = base_url + url
    headers = {}
    headers['Content-Type'] = 'application/json'
    while not success:
        try:
            headers['Authorization'] = 'Bearer ' + get_current_access_token(correlation_id)

            result = requests.put(data=json.dumps(data), url=full_url, headers=headers)
            if result.status_code in [HTTPStatus.OK, HTTPStatus.NO_CONTENT, HTTPStatus.CREATED]:
                success = True
            elif result.status_code == HTTPStatus.UNAUTHORIZED and retry_count <= 1:
                refresh_token(correlation_id)
                retry_count += 1
                # and loop to retry
            else:
                raise Exception(result.status_code)
        except HTTPError as err:
            if err.code == HTTPStatus.UNAUTHORIZED and retry_count <= 1:
                refresh_token(correlation_id)
                retry_count += 1
                # and loop to retry
            else:
                raise err

    return result


def hubspot_delete(url, correlation_id):
    success = False
    retry_count = 0
    full_url = base_url + url
    headers = {}
    headers['Content-Type'] = 'application/json'
    while not success:
        try:
            headers['Authorization'] = 'Bearer ' + get_current_access_token(correlation_id)

            response = requests.delete(url=full_url, headers=headers)
            if response.status_code in [HTTPStatus.OK, HTTPStatus.NO_CONTENT]:
                success = True
            elif response.status_code == HTTPStatus.UNAUTHORIZED and retry_count <= 1:
                refresh_token(correlation_id)
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
                refresh_token(correlation_id)
                retry_count += 1
                # and loop to retry
            else:
                raise err

    return response

# endregion


def get_hubspot_contact():
    url = '/contacts/v1/lists/all/contacts/all'
    return hubspot_get(url, None)


def update_contact(email: str, property_changes: list, correlation_id):
    url = '/contacts/v1/contact/email/' + email + '/profile'

    data = {"properties": property_changes}

    r = hubspot_post(url, data, correlation_id)

    return r.status_code


# region token processing

def get_token_from_database(correlation_id) -> dict:
    try:
        token = get_item('tokens', 'hubspot', correlation_id)['details']
    except:
        token = None
    return token


hubspot_oauth_token = None


def save_token(new_token, correlation_id):
    put_item('tokens', 'hubspot', 'oAuth_token', new_token, {}, True, correlation_id)


def get_current_access_token(correlation_id) -> str:
    global hubspot_oauth_token
    if hubspot_oauth_token is None:
        hubspot_oauth_token = get_token_from_database(correlation_id)
    return hubspot_oauth_token['access_token']


def get_new_token_from_hubspot(refresh_token, code, correlation_id):
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
    save_token(token, correlation_id)
    hubspot_oauth_token = token
    return token


def refresh_token(correlation_id):
    refresh_token = hubspot_oauth_token['refresh_token']
    return get_new_token_from_hubspot(refresh_token, None, correlation_id)


def get_initial_token_from_hubspot():
    code = "305f233c-8f14-43cc-ac1c-a7c629393c5b"   # paste this from thiscovery admin
    return get_new_token_from_hubspot(None, code, None)

hubspot_oauth_token = get_token_from_database(None)

# endregion


def hubspot_timestamp(datetime_string: str):
    # strip milliseconds and timezone
    datetime_string = datetime_string[:19]
    # date string may contain 'T' - if so then replace with space
    datetime_string = datetime_string.replace('T', ' ')
    datetime_value = datetime.strptime(datetime_string, DATE_FORMAT)
    datetime_timestamp = int(datetime_value.timestamp() * 1000)
    return datetime_timestamp


def post_new_user_to_crm(new_user, correlation_id):
    email = new_user['email']

    url = '/contacts/v1/contact/createOrUpdate/email/' + email

    created_timestamp = hubspot_timestamp(new_user['created'])

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

    result = hubspot_post(url, data, correlation_id)

    if result.status_code == HTTPStatus.OK:

        content_str = result.content.decode('utf-8')
        content = json.loads(content_str)
        vid = content['vid']
        is_new = content['isNew']
        return vid, is_new

    else:
        return -1, False


def post_task_signup_to_crm(signup_details, correlation_id):
    tle_type_id = get_TLE_type_id(TASK_SIGNUP_TLE_TYPE_NAME, correlation_id)
    tle_details = {
        'id': signup_details['id'],
        'objectId': signup_details['crm_id'],
        'eventTypeId': tle_type_id,
        'project_id': signup_details['project_id'],
        'project_name': signup_details['project_name'],
        'task_id': signup_details['task_id'],
        'task_name': signup_details['task_name'],
        'task_type_id': signup_details['task_type_id'],
        'task_type_name': signup_details['task_type_name'],
        'signup_event_type': signup_details['signup_event_type'],
        'timestamp': hubspot_timestamp(signup_details['created'])
    }

    return create_or_update_timeline_event(tle_details, correlation_id)


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

    # event_data = {
    #     "id": str(uuid.uuid4()),
    #     "objectId": 1101,
    #     "eventTypeId": "279633",
    #     "study-name": "Test 6 from API with date",
    # }

    # result = create_or_update_timeline_event(event_data)

    # result = delete_timeline_event_type(390568)

    result = create_TLE_for_task_signup()

    # save_TLE_type_id('test', 1234)

    # result = get_TLE_type_id('test')
    print(result)

    # save_token(result_2019_05_10_12_11)