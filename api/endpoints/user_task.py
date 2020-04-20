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
from http import HTTPStatus

import common.sql_queries as sql_q
import common.utilities as utils
from common.pg_utilities import execute_query, execute_non_query
from common.sql_queries import GET_USER_TASK_SQL, UPDATE_USER_TASK_PROGRESS_INFO_SQL, CHECK_IF_USER_TASK_EXISTS_SQL, \
    CREATE_USER_TASK_SQL
from user import get_user_by_id
from project import get_project_task
from user_project import create_user_project_if_not_exists
from common.notification_send import notify_new_task_signup


STATUS_CHOICES = (
    'active',
    'complete',
    'withdrawn',
)
DEFAULT_STATUS = 'active'

# this line is only here to prevent PyCharm from marking these global variables as unresolved; they are reassigned in create_user_project function below
ext_user_task_id, created, status, user_task_url = None, None, None, None


def validate_status(s):
    if s in STATUS_CHOICES:
        return s
    else:
        errorjson = {'status': s}
        raise utils.DetailedValueError('invalid user_task status', errorjson)


def get_user_task(ut_id, correlation_id=None):
    result = execute_query(GET_USER_TASK_SQL, (str(ut_id),), correlation_id)
    return result


def filter_user_tasks_by_project_task_id(user_id, project_task_id, correlation_id=None):
    """
    Returns user_task related to user_id and project_task_id or None
    """
    result = [t for t in list_user_tasks_by_user(user_id, correlation_id) if t['project_task_id'] == project_task_id]
    return result


def calculate_url(base_url, pt_user_specific_url, ut_url, user_id, ut_id, pt_external_task_id, correlation_id=None):
    if pt_user_specific_url:
        base_url = ut_url

    if base_url:
        return "{}{}{}".format(
            base_url,
            utils.create_url_params(user_id, ut_id, pt_external_task_id),
            utils.non_prod_env_url_param()
        )


def list_user_tasks_by_user(user_id, correlation_id=None):

    try:
        user_id = utils.validate_uuid(user_id)
    except utils.DetailedValueError:
        raise

    # check that user exists
    result = get_user_by_id(user_id, correlation_id)
    if len(result) == 0:
        errorjson = {'user_id': user_id, 'correlation_id': str(correlation_id)}
        raise utils.ObjectDoesNotExistError('user does not exist', errorjson)

    result = execute_query(sql_q.LIST_USER_TASKS_SQL, (str(user_id),), correlation_id)

    # add url field to each user_task in result
    edited_result = list()
    for ut in result:
        ut['url'] = calculate_url(ut['base_url'], ut['user_specific_url'], ut['user_task_url'],
                                  ut['user_id'], ut['user_task_id'], ut['external_task_id'], correlation_id)
        del ut['base_url']
        del ut['external_task_id']
        del ut['user_specific_url']
        del ut['user_task_url']
        edited_result.append(ut)

    return edited_result


@utils.lambda_wrapper
@utils.api_error_handler
def list_user_tasks_api(event, context):
    logger = event['logger']
    correlation_id = event['correlation_id']

    parameters = event['queryStringParameters']
    user_id = parameters.get('user_id')

    if not user_id:  # e.g. parameters is None or an empty dict
        errorjson = {'queryStringParameters': parameters, 'correlation_id': str(correlation_id)}
        raise utils.DetailedValueError('This endpoint requires parameter user_id', errorjson)

    project_task_id = parameters.get('project_task_id')

    if project_task_id:
        logger.info('API call', extra={'user_id': user_id, 'project_task_id': project_task_id, 'correlation_id': correlation_id, 'event': event})
        result = filter_user_tasks_by_project_task_id(user_id, project_task_id, correlation_id)
    else:
        logger.info('API call', extra={'user_id': user_id, 'correlation_id': correlation_id, 'event': event})
        result = list_user_tasks_by_user(user_id, correlation_id)

    # todo: this was added here as a way of quickly fixing an issue with the thiscovery frontend; review what to do for the longer term
    if len(result) == 1:
        result = result[0]

    return {"statusCode": HTTPStatus.OK, "body": json.dumps(result)}


def check_if_user_task_exists(user_id, project_task_id, correlation_id):
    return execute_query(CHECK_IF_USER_TASK_EXISTS_SQL, (str(user_id), str(project_task_id)), correlation_id, False)


def create_user_task(ut_json, correlation_id):
    """
    Inserts new UserTask row in thiscovery db

    Args:
        ut_json: must contain user_id, project_task_id and consented; may optionally include id, created, status, ext_user_task_id, user_task_url
        correlation_id:

    Returns:
    """
    # extract mandatory data from json
    try:
        user_id = utils.validate_uuid(ut_json['user_id'])
        project_task_id = utils.validate_uuid(ut_json['project_task_id'])
        consented = utils.validate_utc_datetime(ut_json['consented'])
    except utils.DetailedValueError as err:
        err.add_correlation_id(correlation_id)
        raise err
    except KeyError as err:
        errorjson = {'parameter': err.args[0], 'correlation_id': str(correlation_id)}
        raise utils.DetailedValueError('mandatory data missing', errorjson) from err

    # now process optional json data
    optional_fields_name_default_and_validator = [
        ('ext_user_task_id', str(uuid.uuid4()), utils.validate_uuid),
        ('created', str(utils.now_with_tz()), utils.validate_utc_datetime),
        ('status', DEFAULT_STATUS, validate_status),
        ('user_task_url', None, utils.validate_url)
    ]
    for variable_name, default_value, validating_func in optional_fields_name_default_and_validator:
        if variable_name in ut_json:
            try:
                globals()[variable_name] = validating_func(ut_json[variable_name])  # https://stackoverflow.com/a/4687672
            except utils.DetailedValueError as err:
                err.add_correlation_id(correlation_id)
                raise err
        else:
            globals()[variable_name] = default_value

    # id shadows builtin function, so treat if separately (using globals() approach above would overwrite that function)
    if 'id' in ut_json:
        try:
            id = utils.validate_uuid(ut_json['id'])
        except utils.DetailedValueError as err:
            err.add_correlation_id(correlation_id)
            raise err
    else:
        id = str(uuid.uuid4())

    # get corresponding project_task...
    project_task = get_project_task(project_task_id, correlation_id)
    try:
        pt_ = project_task[0]
    except IndexError:
        errorjson = {'user_id': user_id, 'project_task_id': project_task_id, 'correlation_id': str(correlation_id)}
        raise utils.DetailedIntegrityError('project_task does not exist', errorjson)

    project_id = pt_['project_id']
    base_url = pt_['base_url']
    task_provider_name = pt_['task_provider_name']
    external_task_id = pt_['external_task_id']
    user_specific_url = pt_['user_specific_url']

    # create_user_external_account_if_not_exists(user_id, project_task['external_system_id'], correlation_id)

    user_project = create_user_project_if_not_exists(user_id, project_id, correlation_id)
    user_project_id = user_project['id']

    # check external account does not already exist
    existing = check_if_user_task_exists(user_id, project_task_id, correlation_id)
    # if int(existing[0][0]) > 0:
    if len(existing) > 0:
        errorjson = {'user_id': user_id, 'project_task_id': project_task_id, 'correlation_id': str(correlation_id)}
        raise utils.DuplicateInsertError('user_task already exists', errorjson)

    execute_non_query(
        CREATE_USER_TASK_SQL,
        (id, created, created, user_project_id, project_task_id, status, consented, ext_user_task_id, user_task_url),
        correlation_id
    )

    url = calculate_url(base_url, user_specific_url, user_task_url, user_id, id, external_task_id, correlation_id=correlation_id)

    new_user_task = {
        'id': id,
        'created': created,
        'modified': created,
        'user_id': user_id,
        'user_project_id': user_project_id,
        'project_task_id': project_task_id,
        'task_provider_name': task_provider_name,
        'url': url,
        'status': status,
        'consented': consented,
        'ext_user_task_id': ext_user_task_id,
    }

    notify_new_task_signup(new_user_task, correlation_id)

    return new_user_task


@utils.lambda_wrapper
@utils.api_error_handler
def create_user_task_api(event, context):
    logger = event['logger']
    correlation_id = event['correlation_id']

    ut_json = json.loads(event['body'])
    logger.info('API call', extra={'ut_json': ut_json, 'correlation_id': correlation_id})
    new_user_task = create_user_task(ut_json, correlation_id)
    return {"statusCode": HTTPStatus.CREATED, "body": json.dumps(new_user_task)}


def set_user_task_completed(ut_id, correlation_id=None):
    utils.validate_uuid(ut_id)
    # check that user_task exists
    result = get_user_task(ut_id, correlation_id)
    if len(result) == 0:
        errorjson = {'user_task_id': ut_id, 'correlation_id': str(correlation_id)}
        raise utils.ObjectDoesNotExistError('user task does not exist', errorjson)

    updated_rows_count = execute_non_query(
        sql_q.UPDATE_USER_TASK_STATUS,
        (
            'complete',
            str(utils.now_with_tz()),
            str(ut_id),
        ),
        correlation_id
    )

    assert updated_rows_count == 1, f"Failed to update status of user task {ut_id}; updated_rows_count: {updated_rows_count}"


@utils.lambda_wrapper
@utils.api_error_handler
def set_user_task_completed_api(event, context):
    """
    Third party systems (eg Qualtrics) use this endpoint to inform Thiscovery that a user has completed a task.

    Note that the standard way to do this would be create a json patch entity and implement full patch functionality in
    user_task as in other patchable entities.  We do not have time to develop and test that right now, so please omit this.
    We can come back to it.

    Also, this is fundamentally the wrong approach to be taking to this problem.  We need to be posting events to Thiscovery.
    So this code will be completely superseded in the medium term.
    """
    logger = event['logger']
    correlation_id = event['correlation_id']

    parameters = event['queryStringParameters']
    user_task_id = parameters.get('user_task_id')

    if not user_task_id:  # e.g. parameters is None or an empty dict
        errorjson = {'queryStringParameters': parameters, 'correlation_id': str(correlation_id)}
        raise utils.DetailedValueError('This endpoint requires parameter user_task_id', errorjson)

    logger.info('API call', extra={'user_task_id': user_task_id, 'correlation_id': correlation_id, 'event': event})
    set_user_task_completed(user_task_id, correlation_id)

    return {"statusCode": HTTPStatus.NO_CONTENT}
