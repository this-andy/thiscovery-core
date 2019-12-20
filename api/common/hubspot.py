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
from urllib.request import urlopen, Request
from urllib.error import HTTPError
from http import HTTPStatus
from datetime import datetime


from common.utilities import get_secret, get_logger, get_aws_namespace, DetailedValueError, now_with_tz
from common.dynamodb_utilities import get_item, put_item

DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# use namespace_override to enable using dev hubspot with production Thiscovery
# hubspot_connection = get_secret('hubspot-connection', namespace_override='/dev/')
#
# client_id = hubspot_connection['client-id']
# client_secret = hubspot_connection['client-secret']

base_url = 'https://api.hubapi.com'


TASK_SIGNUP_TLE_TYPE_NAME = 'task-signup'


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


# region common hubspot get/post/put/delete methods

def hubspot_get(url, correlation_id):
    success = False
    retry_count = 0
    full_url = base_url + url
    headers = {}
    headers['Content-Type'] = 'application/json'
    data = None
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
            elif err.code == HTTPStatus.NOT_FOUND:
                return None
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
            elif err.code == HTTPStatus.NOT_FOUND:
                return None
            else:
                raise err

    return response

# endregion

# region hubspot developer get/post/put/delete methods - used for managing TLE definitions

def hubspot_developer_post(url: str, data: dict, correlation_id):
    """
    Posts using developer API key and user id instead of usual oAuth2 token
    This is necessary for creating TLE types
    """
    from api.local.secrets import HUBSPOT_DEVELOPER_APIKEY, HUBSPOT_DEVELOPER_USERID
    hubspot_connection = get_secret('hubspot-connection')
    app_id = hubspot_connection['app-id']

    full_url = base_url + url + \
               '?hapikey=' + HUBSPOT_DEVELOPER_APIKEY + \
               '&userId=' + HUBSPOT_DEVELOPER_USERID + \
               '&application-id=' + app_id
    headers = {'Content-Type': 'application/json'}
    try:
        result = requests.post(data=json.dumps(data), url=full_url, headers=headers)
        if result.status_code in [HTTPStatus.OK, HTTPStatus.CREATED]:
            success = True
        else:
            errorjson = {'result': result}
            raise DetailedValueError('HTTP code ' + str(result.status_code), errorjson)
    except HTTPError as err:
        raise err
    return result


def hubspot_developer_delete(url: str, correlation_id):
    """
    Posts using developer API key and user id instead of usual oAuth2 token
    This is necessary for creating TLE types
    """
    from api.local.secrets import HUBSPOT_DEVELOPER_APIKEY, HUBSPOT_DEVELOPER_USERID
    full_url = base_url + url + \
               '?hapikey=' + HUBSPOT_DEVELOPER_APIKEY + \
               '&userId=' + HUBSPOT_DEVELOPER_USERID
    headers = {'Content-Type': 'application/json'}
    try:
        result = requests.delete(url=full_url, headers=headers)
        if result.status_code in [HTTPStatus.OK, HTTPStatus.NO_CONTENT]:
            success = True
        else:
            errorjson = {'result': result}
            raise DetailedValueError('HTTP code ' + str(result.status_code), errorjson)
    except HTTPError as err:
        raise err
    return result

# endregion


# region contact methods

def get_contact_property(contact, property_name):
    """

    Args:
        contact:
        property_name:

    Returns:
    """
    return contact['properties'][property_name]['value']


def get_hubspot_contact_by_id(id, correlation_id):
    """

    Args:
        id: hubspot ID of contact
        correlation_id:

    Returns:

    """
    url = '/contacts/v1/contact/vid/' + str(id) + '/profile'
    return hubspot_get(url, correlation_id)


def get_hubspot_contact_by_email(email: str, correlation_id):
    url = '/contacts/v1/contact/email/' + str(email) + '/profile'
    return hubspot_get(url, correlation_id)


def get_hubspot_contacts(correlation_id):
    url = '/contacts/v1/lists/all/contacts/all'
    return hubspot_get(url, correlation_id)


def update_contact_core(url, property_changes, correlation_id):
    data = {"properties": property_changes}
    r = hubspot_post(url, data, correlation_id)
    return r.status_code


def update_contact_by_email(email: str, property_changes: list, correlation_id):
    url = '/contacts/v1/contact/email/' + email + '/profile'
    return update_contact_core(url, property_changes, correlation_id)


def update_contact_by_id(hubspot_id, property_changes: list, correlation_id):
    url = '/contacts/v1/contact/vid/' + str(hubspot_id) + '/profile'
    return update_contact_core(url, property_changes, correlation_id)


def delete_hubspot_contact(id, correlation_id):
    url = '/contacts/v1/contact/vid/' + str(id)
    return hubspot_delete(url, correlation_id)


# endregion

# region token processing

def get_token_from_database(correlation_id) -> dict:
    try:
        token = get_item('tokens', 'hubspot', correlation_id)['details']
    except:
        token = None
    return token


# hubspot_oauth_token = None


def save_token(new_token, correlation_id):
    put_item('tokens', 'hubspot', 'oAuth_token', new_token, {}, True, correlation_id)


def get_current_access_token(correlation_id) -> str:
    # global hubspot_oauth_token
    # if hubspot_oauth_token is None:
    hubspot_oauth_token = get_token_from_database(correlation_id)
    return hubspot_oauth_token['access_token']


def get_new_token_from_hubspot(refresh_token, code, redirect_url, correlation_id):

    # global hubspot_oauth_token
    hubspot_connection = get_secret('hubspot-connection')
    client_id = hubspot_connection['client-id']
    client_secret = hubspot_connection['client-secret']

    formData = {
        "client_id": client_id,
        "client_secret": client_secret,
    }

    if redirect_url is not None:
        formData['redirect_uri'] = redirect_url

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
    # hubspot_oauth_token = token
    return token


def refresh_token(correlation_id):
    hubspot_oauth_token = get_token_from_database(None)
    refresh_token = hubspot_oauth_token['refresh_token']
    return get_new_token_from_hubspot(refresh_token, None, None, correlation_id)


def get_initial_token_from_hubspot():
    from common.dev_config import INITIAL_HUBSPOT_AUTH_CODE, NGROK_URL_ID

    redirect_url = 'https://' + NGROK_URL_ID + '.ngrok.io/hubspot'
    return get_new_token_from_hubspot(None, INITIAL_HUBSPOT_AUTH_CODE, redirect_url, None)

# hubspot_oauth_token = get_token_from_database(None)

# endregion

# region hubspot timestamp methods

def hubspot_timestamp(datetime_string: str):
    # strip milliseconds and timezone
    datetime_string = datetime_string[:19]
    # date string may contain 'T' - if so then replace with space
    datetime_string = datetime_string.replace('T', ' ')
    datetime_value = datetime.strptime(datetime_string, DATE_FORMAT)
    datetime_timestamp = int(datetime_value.timestamp() * 1000)
    return datetime_timestamp


def hubspot_timestamp_to_datetime(hubspot_timestamp: int):
    timestamp = hubspot_timestamp/1000
    dt = datetime.fromtimestamp(timestamp)
    return dt
# endregion


def post_new_user_to_crm(new_user, correlation_id):
    """

    Args:
        new_user (json): see test_hubspot.TEST_USER_01 for an example
        correlation_id:

    Returns:
        tuple: (hubspot_id, is_new) if successful, (-1, False) otherwise

    Tested in:
        test_hubspot.test_01_create_contact_ok

    """
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


def post_user_login_to_crm(login_details, correlation_id):
    user_email = login_details['email']
    login_time_str = login_details['login_datetime']
    login_timestamp = hubspot_timestamp(login_time_str)
    property_name = 'thiscovery_last_login_date'
    changes = [
        {"property": property_name, "value": int(login_timestamp)},
    ]
    return update_contact_by_email(user_email, changes, correlation_id)


class TimelineEventsManager:
    def __init__(self, app_id=None):
        # workaround for setting get_secret('hubspot-connection')['app-id'] as default value of app_id. Defining it as default above instead of None breaks
        # the tests that rely on this class because, if that is tried, os.environ["TESTING"] does not exist inside the scope of get_secret.
        if not app_id:
            self.app_id = get_secret('hubspot-connection')['app-id']
        else:
            self.app_id = app_id

    def get_timeline_event(self, tle_type_id, tle_id, correlation_id):
        url = f'/integrations/v1/{self.app_id}/timeline/event/{tle_type_id}/{tle_id}'
        result = hubspot_get(url, correlation_id)
        return result

    def get_timeline_event_properties(self, tle_type_id):
        url = f'/integrations/v1/{self.app_id}/timeline/event-types/{tle_type_id}/properties'
        result = hubspot_get(url, None)
        return result

    def create_or_update_timeline_event(self, event_data: dict, correlation_id):
        url = f'/integrations/v1/{self.app_id}/timeline/event'
        result = hubspot_put(url, event_data, correlation_id)
        return result.status_code

    def create_timeline_event_properties(self, tle_type_id, property_defns: list):
        url = f'/integrations/v1/{self.app_id}/timeline/event-types/{tle_type_id}/properties'
        for property_defn in property_defns:
            hubspot_developer_post(url, property_defn, None)

    def create_timeline_event_type(self, type_defn):
        """
        See https://developers.hubspot.com/docs/methods/timeline/create-event-type

        Args:
            type_defn (dict): see test_hubspot.TEST_TLE_TYPE_DEFINITION for an example

        Returns:
            content['id'] (int): ID of created timeline event type
        """
        type_defn['applicationId'] = self.app_id
        url = f'/integrations/v1/{self.app_id}/timeline/event-types'
        response = hubspot_developer_post(url, type_defn, None)
        content = json.loads(response.content)
        return content['id']

    def delete_timeline_event_property(self, tle_type_id, property_id):
        url = f'/integrations/v1/{self.app_id}/timeline/event-types/{tle_type_id}/properties/{property_id}'
        result = hubspot_delete(url, None)
        return result.status_code

    def delete_timeline_event_type(self, tle_type_id):
        """
        See https://developers.hubspot.com/docs/methods/timeline/delete-event-type

        Args:
            tle_type_id: ID of timeline event type to be deleted

        Returns:
            Status code of delete request: Returns a 204 No Content response on success
        """
        url = f'/integrations/v1/{self.app_id}/timeline/event-types/{tle_type_id}'
        result = hubspot_developer_delete(url, None)
        return result.status_code

    def create_timeline_event_for_task_signup(self):
        type_defn = {
            "name": TASK_SIGNUP_TLE_TYPE_NAME,
            "objectType": "CONTACT",
            "headerTemplate": "{{signup_event_type}} for {{task_name}}",
            "detailTemplate": "Project: {{project_name}}  {{project_id}}\nTask type: {{task_type_name}}  {{task_type_id}}"
        }

        tle_type_id = self.create_timeline_event_type(type_defn)

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

        self.create_timeline_event_properties(tle_type_id, properties)

        save_TLE_type_id(TASK_SIGNUP_TLE_TYPE_NAME, tle_type_id, None)


if __name__ == "__main__":
    pass

    # This line allow you to initialise HubSpot oauth token
    # result = get_initial_token_from_hubspot()

    # and manually refresh it if required
    # result = refresh_token(None)

    # existing_tle_type_id_from_hubspot =
    # save_TLE_type_id(TASK_SIGNUP_TLE_TYPE_NAME, tle_type_id, None)

    # hubspot_id = 1151
    # tsn = hubspot_timestamp(str(now_with_tz()))
    # changes = [
    #         {"property": "thiscovery_registered_date", "value": int(tsn)},
    #     ]
    # result = update_contact_by_id(hubspot_id, changes, None)
    #
    # contact = get_hubspot_contact_by_id(hubspot_id, None)
    #
    # thiscovery_registered_timestamp = get_contact_property(contact, 'thiscovery_registered_date')
    #
    # thiscovery_registered_date = hubspot_timestamp_to_datetime(int(thiscovery_registered_timestamp))
    #
    # print(thiscovery_registered_date)
    #
    # pass


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

    # type_defn = {
    #         "name": "Task sign-up",
    #         "objectType": "CONTACT",
    #         "headerTemplate": "sample header template",
    #         "detailTemplate": "sample detail template"
    #     }

    # result = create_timeline_event_type(type_defn)

    # data = [
    #     {
    #         "name": "project_id",
    #         "label": "Project Id",
    #         "propertyType": "String"
    #     },
    #     {
    #         "name": "project_name",
    #         "label": "Project Name",
    #         "propertyType": "String"
    #     },
    #     {
    #         "name": "task_id",
    #         "label": "Task Id",
    #         "propertyType": "String"
    #     },
    #     {
    #         "name": "task_name",
    #         "label": "Task Name",
    #         "propertyType": "String"
    #     },
    #     {
    #         "name": "task_type_id",
    #         "label": "Task Type Id",
    #         "propertyType": "String"
    #     },
    #     {
    #         "name": "task_type_name",
    #         "label": "Task Type",
    #         "propertyType": "String"
    #     },
    #     {
    #         "name": "signup_event_type",
    #         "label": "Event Type",
    #         "propertyType": "String"
    #     },
    # ]

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

    # result = delete_timeline_event_type(395426)


    # save_TLE_type_id('test', 1234)

    # result = get_TLE_type_id('test')

    # result = get_hubspot_contact(1101, None)
    # result = get_hubspot_contacts()
    # props = result['properties']
    # print(result)

    # save_token(result_2019_05_10_12_11)

    # run these two lines to setup new HubSpot env
    # result = create_thiscovery_contact_properties()
    # result = create_TLE_for_task_signup()
