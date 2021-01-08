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
import traceback
import uuid
from http import HTTPStatus
from datetime import timedelta
from jsonpatch import JsonPatch, JsonPatchException, InvalidJsonPatch

import common.pg_utilities as pg_utils
import common.sql_queries as sql_q
import thiscovery_lib.utilities as utils
from common.pg_utilities import execute_query, execute_jsonpatch, execute_non_query, new_correlation_id
from common.entity_update import EntityUpdate
# from utils import validate_uuid
from common.notification_send import notify_new_user_registration, notify_user_login


def validate_status(s):
    return s


def append_avatar_to_list(user_list):
    for user in user_list:
        append_avatar(user)
    return user_list


def append_avatar(user):
    try:
        first_name = user['first_name']
        last_name = user['last_name']
        if len(first_name) == 0:
            avatar_string = last_name[0:2]
        elif len(last_name) == 0:
            avatar_string = first_name[0:2]
        else:
            avatar_string = first_name[0] + last_name[0]
    except:
        avatar_string = '??'
    user['avatar_string'] = avatar_string
    return user


def append_calculated_properties_to_list(user_list):
    user_list = utils.append_country_name_to_list(user_list)
    user_list = append_avatar_to_list(user_list)
    return user_list


def append_calculated_properties(user):
    utils.append_country_name(user)
    append_avatar(user)
    return user


def get_user_by_anon_project_specific_user_id(anon_project_specific_user_id, correlation_id=None):
    try:
        anon_project_specific_user_id = utils.validate_uuid(anon_project_specific_user_id)
    except utils.DetailedValueError as err:
        err.add_correlation_id(correlation_id)
        raise err

    user_json = execute_query(sql_q.GET_USER_BY_ANON_PROJECT_SPECIFIC_USER_ID_SQL, (str(anon_project_specific_user_id),), correlation_id)

    return append_calculated_properties_to_list(user_json)


def get_user_by_id(user_id, correlation_id=None):

    try:
        user_id = utils.validate_uuid(user_id)
    except utils.DetailedValueError as err:
        err.add_correlation_id(correlation_id)
        raise err

    sql_where_clause = " WHERE id = %s"

    user_json = execute_query(sql_q.BASE_USER_SELECT_SQL + sql_where_clause, (str(user_id),), correlation_id)

    return append_calculated_properties_to_list(user_json)


@utils.lambda_wrapper
@utils.api_error_handler
@pg_utils.db_connection_handler
def get_user_by_id_api(event, context):
    logger = event['logger']
    correlation_id = event['correlation_id']

    user_id = event['pathParameters']['id']
    logger.info('API call', extra={'user_id': user_id, 'correlation_id': correlation_id, 'event': event})

    result = get_user_by_id(user_id, correlation_id)

    if len(result) > 0:
        user_json = result[0]
        # login_info = {
        #     'email': user_json['email'],
        #     'user_id': user_id,
        #     'login_datetime': str(utils.now_with_tz())
        # }
        # notify_user_login(login_info, correlation_id)
        return {"statusCode": HTTPStatus.OK, "body": json.dumps(user_json)}

    else:
        errorjson = {'user_id': user_id, 'correlation_id': str(correlation_id)}
        raise utils.ObjectDoesNotExistError('user does not exist', errorjson)


def get_user_by_email(user_email, correlation_id):
    sql_where_clause = " WHERE email = %s"
    user_json = execute_query(sql_q.BASE_USER_SELECT_SQL + sql_where_clause, (str(user_email),), correlation_id)
    return append_calculated_properties_to_list(user_json)


def list_users_by_project(project_id, logger=None, correlation_id=None):
    if logger is None:
        logger = utils.get_logger()
    users = execute_query(
        base_sql=sql_q.LIST_USERS_BY_PROJECT_SQL,
        params=(project_id,),
        correlation_id=correlation_id
    )
    return users


@utils.lambda_wrapper
@utils.api_error_handler
@pg_utils.db_connection_handler
def list_users_by_project_api(event, context):
    logger = event['logger']
    correlation_id = event['correlation_id']

    parameters = event['queryStringParameters']
    try:
        project_id = parameters['project_id']
    except KeyError:
        errorjson = {'queryStringParameters': parameters, 'correlation_id': str(correlation_id)}
        raise utils.DetailedValueError('This endpoint requires one query parameter (project_id); none were found', errorjson)

    result = list_users_by_project(
        project_id=project_id,
        correlation_id=correlation_id
    )

    return {"statusCode": HTTPStatus.OK, "body": json.dumps(result)}


@utils.lambda_wrapper
@utils.api_error_handler
@pg_utils.db_connection_handler
def get_user_by_email_api(event, context):
    """
    Handler for Lambda function supporting the /v1/user API endpoint. Supports retrieval of user info by email or anon_project_specific_user_id

    Args:
        event (dict): event['queryStringParameters'] may contain either an 'email' or 'anon_project_specific_user_id' parameter, but not both.
        context:

    Returns:
    """
    logger = event['logger']
    correlation_id = event['correlation_id']

    parameters = event['queryStringParameters']

    if not parameters:  # e.g. parameters is None or an empty dict
        errorjson = {'queryStringParameters': parameters, 'correlation_id': str(correlation_id)}
        raise utils.DetailedValueError('This endpoint requires one query parameter (email or anon_project_specific_user_id); none were found', errorjson)
    else:
        user_email = parameters.get('email')
        anon_project_specific_user_id = parameters.get('anon_project_specific_user_id')

    if user_email and anon_project_specific_user_id:
        errorjson = {'user_email': user_email, 'anon_project_specific_user_id': anon_project_specific_user_id, 'correlation_id': str(correlation_id)}
        raise utils.DetailedValueError('Please query by either email or anon_project_specific_user_id, but not both', errorjson)
    elif user_email:
        user_email = user_email.lower()
        logger.info('API call', extra={'user_email': user_email, 'correlation_id': correlation_id, 'event': event})
        result = get_user_by_email(user_email, correlation_id)
    elif anon_project_specific_user_id:
        logger.info('API call', extra={'anon_project_specific_user_id': anon_project_specific_user_id, 'correlation_id': correlation_id, 'event': event})
        result = get_user_by_anon_project_specific_user_id(anon_project_specific_user_id, correlation_id)
    else:
        errorjson = {'queryStringParameters': parameters, 'correlation_id': str(correlation_id)}
        raise utils.DetailedValueError('Query parameters invalid', errorjson)

    if len(result) > 0:
        return {"statusCode": HTTPStatus.OK, "body": json.dumps(result[0])}
    else:
        errorjson = {'user_email': user_email, 'anon_project_specific_user_id': anon_project_specific_user_id, 'correlation_id': str(correlation_id)}
        raise utils.ObjectDoesNotExistError('user does not exist', errorjson)


def patch_user(id_to_update, patch_json, modified_time=utils.now_with_tz(), correlation_id=new_correlation_id()):
    """

    Args:
        id_to_update:
        patch_json:
        modified_time:
        correlation_id:

    Returns:
        Total number of rows updated in RDS database

    """
    mappings = {
        'email': {'table_name': 'public.projects_user', 'column_name': 'email'},
        'email_address_verified': {'table_name': 'public.projects_user', 'column_name': 'email_address_verified'},
        'title': {'table_name': 'public.projects_user', 'column_name': 'title'},
        'first_name': {'table_name': 'public.projects_user', 'column_name': 'first_name'},
        'last_name': {'table_name': 'public.projects_user', 'column_name': 'last_name'},
        'auth0_id': {'table_name': 'public.projects_user', 'column_name': 'auth0_id'},
        'status': {'table_name': 'public.projects_user', 'column_name': 'status'},
        'country_code': {'table_name': 'public.projects_user', 'column_name': 'country_code'},
        'crm_id': {'table_name': 'public.projects_user', 'column_name': 'crm_id'},
    }

    id_column = 'id'

    return execute_jsonpatch(id_column, id_to_update, mappings, patch_json, modified_time, correlation_id)


def create_user_entity_update(user_id, user_jsonpatch, modified, correlation_id):
    try:
        original_user_list = get_user_by_id(user_id, correlation_id)
        original_user = original_user_list[0]
        return EntityUpdate('user', original_user, user_jsonpatch, modified, correlation_id)
    except IndexError as ex:
        errorjson = {'user_id': user_id, 'correlation_id': str(correlation_id)}
        raise utils.ObjectDoesNotExistError('user does not exist', errorjson)
    except JsonPatchException as ex:
        errorjson = {'user_jsonpatch': user_jsonpatch.to_string(), 'correlation_id': str(correlation_id)}
        raise utils.PatchInvalidJsonError('invalid jsonpatch', errorjson)


@utils.lambda_wrapper
@utils.api_error_handler
@pg_utils.db_connection_handler
def patch_user_api(event, context):
    logger = event['logger']
    correlation_id = event['correlation_id']

    # get info supplied to api call
    user_id = event['pathParameters']['id']
    try:
        user_jsonpatch = JsonPatch.from_string(event['body'])
    except InvalidJsonPatch:
        raise utils.DetailedValueError('invalid jsonpatch', details={
            'traceback': traceback.format_exc(),
            'correlation_id': correlation_id,
        })

    # convert email to lowercase
    for p in user_jsonpatch:
        if p.get('path') == '/email':
            p['value'] = p['value'].lower()

    logger.info('API call', extra={'user_id': user_id, 'user_jsonpatch': user_jsonpatch, 'correlation_id': correlation_id, 'event': event})

    modified_time = utils.now_with_tz()

    # create an audit record of update, inc 'undo' patch
    entity_update = create_user_entity_update(user_id, user_jsonpatch, modified_time, correlation_id)
    patch_user(user_id, user_jsonpatch, modified_time, correlation_id)
    # on successful update save audit record
    entity_update.save()
    return {"statusCode": HTTPStatus.NO_CONTENT, "body": json.dumps('')}


# User create JSON should look like this:
#   {
#     "id": "48e30e54-b4fc-4303-963f-2943dda2b139",
#     "created": "2018-08-21T11:16:56+01:00",
#     "email": "sw@email.addr",
#     "title": "Mr",
#     "first_name": "Steven",
#     "last_name": "Walcorn",
#     "auth0_id": "1234abcd",
#     "status": "new"
#   }

def create_user(user_json, correlation_id):
    # json MUST contain: email, first_name, last_name, status
    # json may OPTIONALLY include: id, title, created, auth0_id
    # note that users will always be created with email_address_verified = false

    # extract mandatory data from json
    try:
        email = user_json['email'].lower()
        first_name = user_json['first_name']
        last_name = user_json['last_name']
        status = validate_status(user_json['status'])
        country_code = user_json['country_code']
        utils.get_country_name(country_code)
        # looking up the name is a way of validating the code - an invalid code will raise an error
    except utils.DetailedValueError as err:
        err.add_correlation_id(correlation_id)
        raise err


    # now process optional json data
    if 'id' in user_json:
        try:
            id = utils.validate_uuid(user_json['id'])
        except utils.DetailedValueError as err:
            err.add_correlation_id(correlation_id)
            raise err
    else:
        id = str(uuid.uuid4())

    if 'created' in user_json:
        try:
            created = utils.validate_utc_datetime(user_json['created'])
        except utils.DetailedValueError as err:
            err.add_correlation_id(correlation_id)
            raise err
    else:
        created = str(utils.now_with_tz())

    if 'auth0_id' in user_json:
        auth0_id = user_json['auth0_id']
    else:
        auth0_id = None

    if 'title' in user_json:
        title = user_json['title']
    else:
        title = None

    existing_user = get_user_by_id(id, correlation_id)
    if len(existing_user) > 0:
        errorjson = {'id': id, 'correlation_id': str(correlation_id)}
        raise utils.DuplicateInsertError('user already exists', errorjson)

    params = (id, created, created, email, title, first_name, last_name, country_code, auth0_id, status)
    execute_non_query(sql_q.CREATE_USER_SQL, params, correlation_id)

    new_user = {
        'id': id,
        'created': created,
        'modified': created,        
        'email': email,
        'title': title,
        'first_name': first_name,
        'last_name': last_name,
        'auth0_id': auth0_id,
        'crm_id': None,
        'country_code': country_code,
        'status': status,
    }

    new_user = append_calculated_properties(new_user)

    try:
        notify_new_user_registration(new_user, correlation_id)
    except Exception as ex:
        raise ex

    return new_user


@utils.lambda_wrapper
@utils.api_error_handler
@pg_utils.db_connection_handler
def create_user_api(event, context):
    logger = event['logger']
    correlation_id = event['correlation_id']

    user_json = json.loads(event['body'])
    logger.info('API call', extra={'user_json': user_json, 'correlation_id': correlation_id, 'event': event})
    new_user = create_user(user_json, correlation_id)
    return {"statusCode": HTTPStatus.CREATED, "body": json.dumps(new_user)}


@utils.lambda_wrapper
def record_user_login_event(event, context):
    namespace = utils.get_aws_namespace()
    logger = event['logger']
    logger.info('API call', extra={'namespace': namespace, 'event': event})

    # Note that Auth0 event log sources are either prod or staging. If this code is being invoked in other environments then
    # it is because events are being forwarded for dev/test purposes.  In this scenario the user referred to in the event will
    # not exist in this environment's RDS database or HubSpot database.  So ignore.
    if namespace in ['/prod/', '/staging/']:
        # event will contain an Auth0 event of type 's''
        event_id = event['id']   # note that event id will be used as correlation id for subsequent processing
        detail_data = event['detail']['data']
        event_type = detail_data['type']
        login_datetime = detail_data['date'].replace('T', ' ').replace('Z', '')
        user_email = detail_data['user_name']
        user_id = get_user_by_email(user_email, event_id)
        login_info = {
            'email': user_email,
            'user_id': user_id,
            'login_datetime': login_datetime
        }
        notify_user_login(login_info, event_id)
        return {"statusCode": HTTPStatus.OK, "body": json.dumps('')}
