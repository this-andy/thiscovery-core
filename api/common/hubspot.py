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

import common.dynamodb_utilities as ddb
from common.utilities import get_secret, get_logger, get_aws_namespace, DetailedValueError, now_with_tz

DATE_FORMAT = '%Y-%m-%d %H:%M:%S'

# use namespace_override to enable using dev hubspot with production Thiscovery
# hubspot_connection = get_secret('hubspot-connection', namespace_override='/dev/')
#
# client_id = hubspot_connection['client-id']
# client_secret = hubspot_connection['client-secret']

BASE_URL = 'https://api.hubapi.com'
CONTACTS_ENDPOINT = '/contacts/v1'
TASK_SIGNUP_TLE_TYPE_NAME = 'task-signup'


class HubSpotClient:

    def __init__(self, correlation_id=None):
        self.correlation_id = correlation_id
        self.tokens = self.get_token_from_database()
        self.access_token = self.tokens['access_token']
        self.refresh_token = self.tokens['refresh_token']
        self.headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.access_token}',
        }
        self.connection_secret = None
        self.app_id = None

    # region token management
    def get_token_from_database(self):
        try:
            return ddb.get_item('tokens', 'hubspot', self.correlation_id)['details']
        except:
            logger = get_logger()
            logger.warning('could not retrieve hubspot token from dynamodb')
            return None

    def get_hubspot_connection_secret(self):
        """
        Fetches HubSpot connection secret from AWS (or from class instance if fetched previously).

        Returns:
            HubSpot connection secret
        """
        if self.connection_secret is None:
            self.connection_secret = get_secret('hubspot-connection')
            self.app_id = self.connection_secret['app-id']
        return self.connection_secret

    def get_new_token_from_hubspot(self, refresh_token='self value', code=None, redirect_url=None, correlation_id=None):
        """
        Use this function to renew the HubSpot token.

        Args:
            refresh_token: HubSpot refresh token stored in AWS Secrets Manager; default value maps to self.refresh_token
            code: HubSpot authorization code required to obtain initial token (one-off use)
            redirect_url: URL for authorization code delivery (one-off use)
            correlation_id: Correlation id for tracing

        Returns:
            Dict of HubSpot credentials, containing values for keys 'access_token', 'refresh_token' and 'app-id'

        Notes:
            Saves the values of 'access_token', 'refresh_token' and 'app-id' to class instance attributes
        """
        if refresh_token == 'self value':
            refresh_token = self.refresh_token
        if correlation_id is None:
            correlation_id = self.correlation_id

        hubspot_connection = self.get_hubspot_connection_secret()
        client_id = hubspot_connection['client-id']
        client_secret = hubspot_connection['client-secret']
        self.app_id = hubspot_connection['app-id']

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
        self.tokens = res.json()
        self.access_token = self.tokens['access_token']
        self.refresh_token = self.tokens['refresh_token']
        self.headers['Authorization'] = f'Bearer {self.access_token}'

        self.save_token(self.tokens, correlation_id)
        return {**self.tokens, 'app-id': self.app_id}

    def get_initial_token_from_hubspot(self):
        """
        One-off function to obtain initial HubSpot token

        Returns:
            HubSpot token (dict), containing values for keys 'access_token' and 'refresh_token'
        """
        from common.dev_config import INITIAL_HUBSPOT_AUTH_CODE, NGROK_URL_ID

        redirect_url = 'https://' + NGROK_URL_ID + '.ngrok.io/hubspot'
        return self.get_new_token_from_hubspot(None, INITIAL_HUBSPOT_AUTH_CODE, redirect_url, None)

    @staticmethod
    def save_token(new_token, correlation_id):
        ddb.put_item('tokens', 'hubspot', 'oAuth_token', new_token, {}, True, correlation_id)
    # endregion

    # region get/post/put/delete requests
    def hubspot_request(self, method, url, params={}, data={}, correlation_id=None):
        if correlation_id is None:
            correlation_id = self.correlation_id
        success = False
        retry_count = 0
        full_url = BASE_URL + url
        while not success:
            try:
                result = requests.request(
                    method=method,
                    url=full_url,
                    params=params,
                    headers=self.headers,
                    data=json.dumps(data),
                )
                if method in ['POST', 'PUT', 'DELETE']:
                    if result.status_code in [HTTPStatus.OK, HTTPStatus.NO_CONTENT, HTTPStatus.CREATED]:
                        success = True
                    elif result.status_code == HTTPStatus.UNAUTHORIZED and retry_count <= 1:
                        self.get_new_token_from_hubspot(self.refresh_token, correlation_id)
                        retry_count += 1
                        # and loop to retry
                    else:
                        errorjson = {'url': url, 'result': result, 'content': result.content}
                        raise DetailedValueError('HTTP code ' + str(result.status_code), errorjson)
                elif method in ['GET']:
                    result = result.json()
                    success = True
                else:
                    raise DetailedValueError(f'Support for method {method} not implemented in {__file__}')

            #TODO: it is now probably ok to remove the try statement and the exception handling code below. Test if that is indeed the case.
            except HTTPError as err:
                if err.code == HTTPStatus.UNAUTHORIZED and retry_count <= 1:
                    self.get_new_token_from_hubspot(self.refresh_token, correlation_id)
                    retry_count += 1
                    # and loop to retry
                else:
                    raise err

            return result

    def post(self, url: str, data: dict, correlation_id):
        return self.hubspot_request('POST', url, data=data, correlation_id=correlation_id)

    def get(self, url, correlation_id):
        return self.hubspot_request('GET', url, correlation_id=correlation_id)

    def put(self, url: str, data: dict, correlation_id):
        return self.hubspot_request('PUT', url, data=data, correlation_id=correlation_id)

    def delete(self, url, correlation_id):
        return self.hubspot_request('DELETE', url, correlation_id=correlation_id)
    # endregion

    # region hubspot developer get/post/put/delete methods - used for managing TLE definitions
    def hubspot_dev_request(self, method, url, data={}, correlation_id=None):
        """
        Make requests using developer API key and user id instead of usual oAuth2 token
        This is necessary for creating TLE types
        """
        from api.local.secrets import HUBSPOT_DEVELOPER_APIKEY, HUBSPOT_DEVELOPER_USERID
        if self.app_id is None:
            self.get_hubspot_connection_secret()
        params = {
            'hapikey': HUBSPOT_DEVELOPER_APIKEY,
            'userId': HUBSPOT_DEVELOPER_USERID,
            'application-id': self.app_id,
        }
        return self.hubspot_request(method, url, params=params, data=data, correlation_id=correlation_id)

    def developer_post(self, url: str, data: dict, correlation_id):
        return self.hubspot_dev_request('POST', url, data=data, correlation_id=correlation_id)

    def developer_delete(self, url: str, correlation_id):
        return self.hubspot_dev_request('DELETE', url, correlation_id=correlation_id)
    # endregion

    # region Contacts API methods
    def get_hubspot_contacts(self, correlation_id):
        url = f'{CONTACTS_ENDPOINT}/lists/all/contacts/all'
        return self.get(url, correlation_id)

    def get_hubspot_contact_by_id(self, id_, correlation_id):
        url = f'{CONTACTS_ENDPOINT}/contact/vid/{id_}/profile'
        return self.get(url, correlation_id)

    def get_hubspot_contact_by_email(self, email: str, correlation_id):
        url = f'{CONTACTS_ENDPOINT}/contact/email/{email}/profile'
        return self.get(url, correlation_id)

    @staticmethod
    def get_contact_property(contact, property_name):
        return contact['properties'][property_name]['value']

    def update_contact_core(self, url, property_changes, correlation_id):
        data = {"properties": property_changes}
        r = self.post(url, data, correlation_id)
        return r.status_code

    def update_contact_by_email(self, email: str, property_changes: list, correlation_id):
        url = f'{CONTACTS_ENDPOINT}/contact/email/{email}/profile'
        return self.update_contact_core(url, property_changes, correlation_id)

    def update_contact_by_id(self, hubspot_id, property_changes: list, correlation_id):
        url = f'{CONTACTS_ENDPOINT}/contact/vid/{hubspot_id}/profile'
        return self.update_contact_core(url, property_changes, correlation_id)

    def delete_hubspot_contact(self, id_, correlation_id):
        url = f'{CONTACTS_ENDPOINT}/contact/vid/{id_}'
        return self.delete(url, correlation_id)
    # endregion

    #region Timeline event types
    @staticmethod
    def get_timeline_event_type_id(name: str, correlation_id):
        table_id = get_aws_namespace() + name
        item = ddb.get_item('lookups', table_id, correlation_id)
        return item['details']['hubspot_id']

    def get_timeline_event_type_properties(self, tle_type_id):
        url = f'/integrations/v1/{self.app_id}/timeline/event-types/{tle_type_id}/properties'
        result = self.get(url, None)
        return result

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
        response = self.dev_post(url, type_defn, None)
        content = json.loads(response.content)
        return content['id']

    def create_timeline_event_type_properties(self, tle_type_id, property_defns: list):
        url = f'/integrations/v1/{self.app_id}/timeline/event-types/{tle_type_id}/properties'
        for property_defn in property_defns:
            self.dev_post(url, property_defn, None)

    def delete_timeline_event_type_property(self, tle_type_id, property_id):
        url = f'/integrations/v1/{self.app_id}/timeline/event-types/{tle_type_id}/properties/{property_id}'
        result = self.delete(url, None)
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
        result = self.dev_delete(url, None)
        return result.status_code

    @staticmethod
    def save_timeline_event_type_id(name: str, hubspot_id, correlation_id):
        table_id = get_aws_namespace() + name
        details = {
            'hubspot_id': str(hubspot_id),
            'name': str(name),
        }
        ddb.put_item('lookups', table_id, 'tle_type', details, {}, True, correlation_id)
    # endregion

    # region Timeline event instances
    def get_timeline_event(self, tle_type_id, tle_id, correlation_id):
        url = f'/integrations/v1/{self.app_id}/timeline/event/{tle_type_id}/{tle_id}'
        result = self.get(url, correlation_id)
        return result

    def create_or_update_timeline_event(self, event_data: dict, correlation_id):
        url = f'/integrations/v1/{self.app_id}/timeline/event'
        result = self.put(url, event_data, correlation_id)
        return result.status_code
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
    hs_client = HubSpotClient()
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

    result = hs_client.post(url=url, data=data, correlation_id=correlation_id)

    if result.status_code == HTTPStatus.OK:

        content_str = result.content.decode('utf-8')
        content = json.loads(content_str)
        vid = content['vid']
        is_new = content['isNew']
        return vid, is_new

    else:
        return -1, False


def post_task_signup_to_crm(signup_details, correlation_id):
    tle_type_manager = TimelineEventTypeManager()
    tle_type_id = tle_type_manager.get_timeline_event_type_id(TASK_SIGNUP_TLE_TYPE_NAME, correlation_id)
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

    return tle_type_manager.create_or_update_timeline_event(tle_details, correlation_id)


def post_user_login_to_crm(login_details, correlation_id):
    contacts_client = ContactsApiClient()
    user_email = login_details['email']
    login_time_str = login_details['login_datetime']
    login_timestamp = hubspot_timestamp(login_time_str)
    property_name = 'thiscovery_last_login_date'
    changes = [
        {"property": property_name, "value": int(login_timestamp)},
    ]
    return contacts_client.update_contact_by_email(user_email, changes, correlation_id)
