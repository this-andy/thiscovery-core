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

import uuid
import json
from http import HTTPStatus
from api.common.pg_utilities import execute_query, execute_non_query
from api.common.utilities import DuplicateInsertError, ObjectDoesNotExistError, DetailedValueError, DetailedIntegrityError, \
    validate_uuid, validate_utc_datetime, get_correlation_id, get_logger, error_as_response_body, now_with_tz, get_start_time, get_elapsed_ms
from api.endpoints.user import get_user_by_id
from api.endpoints.project import get_project_task
from api.endpoints.user_project import create_user_project_if_not_exists


STATUS_CHOICES = (
    'active',
    'complete',
    'withdrawn',
)
DEFAULT_STATUS = 'active'


def validate_status(s):
    if s in STATUS_CHOICES:
        return s
    else:
        errorjson = {'status': s}
        raise DetailedValueError('invalid user_task status', errorjson)


def get_user_task(ut_id, correlation_id):

    base_sql = '''
        SELECT 
            id,
            user_project_id,
            project_task_id,
            created,
            modified,               
            status,
            consented                
        FROM 
            public.projects_usertask
        WHERE id = %s
    '''

    return execute_query(base_sql, (str(ut_id),), correlation_id)


def list_user_tasks(user_id, correlation_id):

    try:
        user_id = validate_uuid(user_id)
    except DetailedValueError:
        raise

    # check that user exists
    result = get_user_by_id(user_id, correlation_id)
    if len(result) == 0:
        errorjson = {'user_id': user_id, 'correlation_id': str(correlation_id)}
        raise ObjectDoesNotExistError('user does not exist', errorjson)

    base_sql = '''
        SELECT 
            up.user_id,
            ut.user_project_id,
            up.status as user_project_status,
            ut.project_task_id,
            pt.description as task_description,
            ut.id as user_task_id,
            ut.created,
            ut.modified,               
            ut.status,
            ut.consented                
        FROM 
            public.projects_usertask ut
            inner join public.projects_projecttask pt on pt.id = ut.project_task_id
            inner join public.projects_userproject up on up.id = ut.user_project_id
        WHERE up.user_id = %s
        ORDER BY ut.created
    '''

    return execute_query(base_sql, (str(user_id),), correlation_id)


def list_user_tasks_api(event, context):
    start_time = get_start_time()
    logger = get_logger()
    correlation_id = None

    try:
        params = event['queryStringParameters']
        user_id = params['user_id']
        correlation_id = get_correlation_id(event)
        logger.info('API call', extra={'user_id': user_id, 'correlation_id': correlation_id})

        response = {
            "statusCode": HTTPStatus.OK,
            "body": json.dumps(list_user_tasks(user_id, correlation_id))
        }

    except ObjectDoesNotExistError as err:
        response = {"statusCode": HTTPStatus.NOT_FOUND, "body": err.as_response_body()}

    except DetailedValueError as err:
        response = {"statusCode": HTTPStatus.BAD_REQUEST, "body": err.as_response_body()}

    except Exception as ex:
        errorMsg = ex.args[0]
        logger.error(errorMsg, extra={'correlation_id': correlation_id})
        response = {"statusCode": HTTPStatus.INTERNAL_SERVER_ERROR, "body": error_as_response_body(errorMsg, correlation_id)}

    logger.info('API response',
                extra={'response': response, 'correlation_id': correlation_id, 'event': event, 'elapsed_ms': get_elapsed_ms(start_time)})
    return response


def check_if_user_task_exists_ORIGINAL(user_project_id, project_task_id, correlation_id):

    base_sql = '''
      SELECT 
        COUNT(id)
      FROM public.projects_usertask 
      WHERE
        user_project_id = %s
        AND project_task_id = %s
    '''

    return execute_query(base_sql, (str(user_project_id), str(project_task_id)), correlation_id, False)


def check_if_user_task_exists(user_id, project_task_id, correlation_id):
    base_sql = '''
      SELECT 
        ut.id
      FROM projects_usertask ut
      JOIN projects_userproject up on ut.user_project_id = up.id
      WHERE
        up.user_id = %s
        AND ut.project_task_id = %s
    '''

    return execute_query(base_sql, (str(user_id), str(project_task_id)), correlation_id, False)


def create_user_task_ORIGINAL(ut_json, correlation_id):
    # json MUST contain: user_project_id, project_task_id, ut_status, ut_consented
    # json may OPTIONALLY include: id, created,

    # extract mandatory data from json
    try:
        user_project_id = validate_uuid(ut_json['user_project_id'])
        project_task_id = validate_uuid(ut_json['project_task_id'])
        ut_status = validate_status(ut_json['status'])
        ut_consented = validate_utc_datetime(ut_json['consented'])
    except DetailedValueError as err:
        err.add_correlation_id(correlation_id)
        raise err

    # now process optional json data
    if 'id' in ut_json:
        try:
            id = validate_uuid(ut_json['id'])
        except DetailedValueError as err:
            err.add_correlation_id(correlation_id)
            raise err
    else:
        id = str(uuid.uuid4())

    if 'created' in ut_json:
        try:
            created = validate_utc_datetime(ut_json['created'])
        except DetailedValueError as err:
            err.add_correlation_id(correlation_id)
            raise err
    else:
        created = str(now_with_tz())

    # check external account does not already exist
    existing = check_if_user_task_exists(user_project_id, project_task_id, correlation_id)
    if int(existing[0][0]) > 0:
        errorjson = {'user_project_id': user_project_id, 'project_task_id': project_task_id, 'correlation_id': str(correlation_id)}
        raise DuplicateInsertError('user_task already exists', errorjson)

    sql = '''INSERT INTO public.projects_usertask (
            id,
            created,
            modified,
            user_project_id,
            project_task_id,
            status,
            consented
        ) VALUES ( %s, %s, %s, %s, %s, %s, %s );'''

    execute_non_query(sql, (id, created, created, user_project_id, project_task_id, ut_status, ut_consented), correlation_id)

    new_user_task = {
        'id': id,
        'created': created,
        'modified': created,
        'user_project_id': user_project_id,
        'project_task_id': project_task_id,
        'status': ut_status,
        'consented': ut_consented,
    }

    return new_user_task


def create_user_task(ut_json, correlation_id):
    # json MUST contain: user_id, project_task_id, ut_consented
    # json may OPTIONALLY include: id, created, ut_status

    # extract mandatory data from json
    try:
        user_id = validate_uuid(ut_json['user_id'])
        project_task_id = validate_uuid(ut_json['project_task_id'])
        ut_consented = validate_utc_datetime(ut_json['consented'])
    except DetailedValueError as err:
        err.add_correlation_id(correlation_id)
        raise err
    except KeyError as err:
        errorjson = {'parameter': err.args[0], 'correlation_id': str(correlation_id)}
        raise DetailedValueError('mandatory data missing', errorjson) from err

    # now process optional json data
    if 'id' in ut_json:
        try:
            id = validate_uuid(ut_json['id'])
        except DetailedValueError as err:
            err.add_correlation_id(correlation_id)
            raise err
    else:
        id = str(uuid.uuid4())

    if 'created' in ut_json:
        try:
            created = validate_utc_datetime(ut_json['created'])
        except DetailedValueError as err:
            err.add_correlation_id(correlation_id)
            raise err
    else:
        created = str(now_with_tz())

    if 'status' in ut_json:
        try:
            ut_status = validate_status(ut_json['status'])
        except DetailedValueError as err:
            err.add_correlation_id(correlation_id)
            raise err
    else:
        ut_status = DEFAULT_STATUS

    # get corresponding project_task...
    project_task = get_project_task(project_task_id, correlation_id)
    try:
        project_id = project_task[0]['project_id']
    except:
        errorjson = {'user_id': user_id, 'project_task_id': project_task_id, 'correlation_id': str(correlation_id)}
        raise DetailedIntegrityError('project_task does not exist', errorjson)

    # create_user_external_account_if_not_exists(user_id, project_task['external_system_id'], correlation_id)

    user_project = create_user_project_if_not_exists(user_id, project_id, correlation_id)
    user_project_id = user_project['id']

    # check external account does not already exist
    existing = check_if_user_task_exists(user_id, project_task_id, correlation_id)
    # if int(existing[0][0]) > 0:
    if len(existing) > 0:
        errorjson = {'user_id': user_id, 'project_task_id': project_task_id, 'correlation_id': str(correlation_id)}
        raise DuplicateInsertError('user_task already exists', errorjson)

    sql = '''INSERT INTO public.projects_usertask (
            id,
            created,
            modified,
            user_project_id,
            project_task_id,
            status,
            consented
        ) VALUES ( %s, %s, %s, %s, %s, %s, %s );'''

    execute_non_query(sql, (id, created, created, user_project_id, project_task_id, ut_status, ut_consented), correlation_id)

    new_user_task = {
        'id': id,
        'created': created,
        'modified': created,
        'user_id': user_id,
        'user_project_id': user_project_id,
        'project_task_id': project_task_id,
        'status': ut_status,
        'consented': ut_consented,
    }

    return new_user_task


def create_user_task_api(event, context):
    start_time = get_start_time()
    logger = get_logger()
    correlation_id = None

    try:
        ut_json = json.loads(event['body'])
        correlation_id = get_correlation_id(event)
        logger.info('API call', extra={'ut_json': ut_json, 'correlation_id': correlation_id})

        new_user_task = create_user_task(ut_json, correlation_id)

        response = {"statusCode": HTTPStatus.CREATED, "body": json.dumps(new_user_task)}

    except DuplicateInsertError as err:
        response = {"statusCode": HTTPStatus.CONFLICT, "body": err.as_response_body()}

    except (DetailedIntegrityError, DetailedValueError) as err:
        response = {"statusCode": HTTPStatus.BAD_REQUEST, "body": err.as_response_body()}

    except Exception as ex:
        error_msg = ex.args[0]
        logger.error(error_msg, extra={'correlation_id': correlation_id})
        response = {"statusCode": HTTPStatus.INTERNAL_SERVER_ERROR, "body": error_as_response_body(error_msg, correlation_id)}

    logger.info('API response',
                extra={'response': response, 'correlation_id': correlation_id, 'event': event, 'elapsed_ms': get_elapsed_ms(start_time)})
    return response


if __name__ == "__main__":
    ut_json = {
        'user_id': "0bef3b7e-ab4a-437e-936a-6b7b557fb059",
        'project_task_id': "273b420e-09cb-419c-8b57-b393595dba78",
        'consented': '2018-06-12 16:16:56.087895+01'
    }
    # print(ut_json)

    ev = {'body': json.dumps(ut_json)}
    print(create_user_task_api(ev, None))

    # print(list_user_tasks("851f7b34-f76c-49de-a382-7e4089b744e2", None))