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
from http import HTTPStatus

import common.sql_queries as sql_q
import common.utilities as utils
from common.pg_utilities import execute_query, execute_query_multiple, dict_from_dataset, execute_non_query


def list_projects(correlation_id):
    return execute_query(sql_q.LIST_PROJECTS_SQL, None, correlation_id)


def list_projects_with_tasks(correlation_id):
    result = execute_query(sql_q.BASE_PROJECT_SELECT_SQL, None, correlation_id, True, False)
    return result


@utils.lambda_wrapper
@utils.api_error_handler
def list_projects_api(event, context):
    logger = event['logger']
    correlation_id = event['correlation_id']

    logger.info('API call', extra={'correlation_id': correlation_id, 'event': event})
    return {
        "statusCode": HTTPStatus.OK,
        "body": json.dumps(list_projects_with_tasks(correlation_id))
    }


def get_project_task(project_task_id, correlation_id=None):
    return execute_query(sql_q.GET_PROJECT_TASK_SQL, (str(project_task_id),), correlation_id)


def update_project_task_progress_info(project_task_id, progress_info_dict, progress_info_modified, correlation_id):
    progress_info_json = json.dumps(progress_info_dict)
    number_of_updated_rows = execute_non_query(sql_q.UPDATE_PROJECT_TASK_SQL, [progress_info_json, progress_info_modified, project_task_id], correlation_id)
    return number_of_updated_rows


def get_project_with_tasks(project_uuid, correlation_id):
    # take base sql query and insert a where clause to get specified project
    sql_where_clause = " AND id = %s "
    # put where clause before final order by
    order_by_index = sql_q.BASE_PROJECT_SELECT_SQL.rfind('order by')
    sql = sql_q.BASE_PROJECT_SELECT_SQL[:order_by_index] + sql_where_clause + sql_q.BASE_PROJECT_SELECT_SQL[order_by_index:]
    result = execute_query(sql, (str(project_uuid),), correlation_id, True, False)

    return result


def get_project_task_by_external_task_id(external_task_id, correlation_id=None):
    return execute_query(sql_q.TASKS_BY_EXTERNAL_ID_SQL, (str(external_task_id),), correlation_id)


@utils.lambda_wrapper
@utils.api_error_handler
def get_project_api(event, context):
    logger = event['logger']
    correlation_id = event['correlation_id']

    project_id = event['pathParameters']['id']
    logger.info('API call', extra={'project_id': project_id, 'correlation_id': correlation_id, 'event': event})

    result = get_project_with_tasks(project_id, correlation_id)

    if len(result) > 0:
        return {"statusCode": HTTPStatus.OK, "body": json.dumps(result)}
    else:
        errorjson = {'project_id': project_id, 'correlation_id': str(correlation_id)}
        raise utils.ObjectDoesNotExistError('project is planned or does not exist', errorjson)


def get_project_status_for_user(user_id, correlation_id, anonymise_url=False):

    project_list = execute_query(sql_q.PROJECT_USER_SELECT_SQL, None, correlation_id, True, False)

    str_user_id = (str(user_id),)
    results = execute_query_multiple(
        (sql_q.get_project_status_for_user_sql['sql0'], sql_q.get_project_status_for_user_sql['sql1'], sql_q.get_project_status_for_user_sql['sql2'],
         sql_q.get_project_status_for_user_sql['sql3'], sql_q.get_project_status_for_user_sql['sql4'], sql_q.get_project_status_for_user_sql['sql5']),
        (str_user_id,)*6,
        correlation_id
    )

    project_group_users_dict = dict_from_dataset(results[0], 'project_id')
    project_testgroup_users_dict = dict_from_dataset(results[1], 'project_id')
    projecttask_group_users_dict = dict_from_dataset(results[2], 'project_task_id')
    projecttask_testgroup_users_dict = dict_from_dataset(results[3], 'project_task_id')
    projects_usertasks_dict = dict_from_dataset(results[4], 'project_task_id')
    user_first_name = results[5][0]['first_name']

    # now add calculated attributes to returned json...
    try:
        for project in project_list:
            project_id = project['id']
            project['project_is_visible'] = \
                ((project['status'] == 'testing') and (project_testgroup_users_dict.get(project_id) is not None)) \
                or ((project['status'] != 'testing') and
                    ((project['visibility'] == 'public') or
                    (project_group_users_dict.get(project_id) is not None)))
            for task in project['tasks']:
                task_id = task['id']
                task['task_is_visible'] = \
                    project['project_is_visible'] and (
                        (task['visibility'] == 'public')
                        or ((task['status'] == 'testing') and (projecttask_testgroup_users_dict.get(task_id) is not None))
                        or ((task['status'] != 'testing') and (projecttask_group_users_dict.get(task_id) is not None)))
                task['user_is_signedup'] = projects_usertasks_dict.get(task_id) is not None
                task['signup_available'] = \
                    (task['task_is_visible'] and (task['status'] == 'active') and not task['user_is_signedup'] and (task['signup_status'] == 'open')) \
                    or (task['task_is_visible'] and (task['status'] == 'testing') and not task['user_is_signedup'])
                if task['user_is_signedup']:
                    if task['status'] == 'complete':
                        task['user_task_status'] = 'complete'
                    else:
                        task['user_task_status'] = projects_usertasks_dict[task_id]['status']
                # only give url if user has signedup (inc if completed)
                if task['task_is_visible'] and task['user_is_signedup']:
                    if task['user_specific_url']:
                        task['url'] = "{}{}".format(
                            projects_usertasks_dict[task_id]['user_task_url'],
                            utils.non_prod_env_url_param()
                        )
                    elif task['url'] is not None:
                        user_task_id = projects_usertasks_dict[task_id]['id']
                        external_task_id = task['external_task_id']
                        ext_user_project_id = projects_usertasks_dict[task_id]['ext_user_project_id']
                        ext_user_task_id = projects_usertasks_dict[task_id]['ext_user_task_id']
                        if anonymise_url:
                            task['url'] += utils.create_anonymous_url_params(ext_user_project_id, ext_user_task_id, external_task_id)
                        else:
                            task['url'] += utils.create_url_params(user_id, user_first_name, user_task_id, external_task_id)
                        task['url'] += utils.non_prod_env_url_param()
                else:
                    task['url'] = None
                    # task['task_provider_name'] = None
    except Exception as ex:
        raise ex

    return project_list


@utils.lambda_wrapper
@utils.api_error_handler
def get_project_status_for_user_api(event, context):
    logger = event['logger']
    correlation_id = event['correlation_id']

    params = event['queryStringParameters']
    user_id = utils.validate_uuid(params['user_id'])
    logger.info('API call', extra={'user_id': user_id, 'correlation_id': correlation_id, 'event': event})
    if user_id == '760f4e4d-4a3b-4671-8ceb-129d81f9d9ca':
        raise ValueError('Deliberate error raised to test error handling')
    return {
        "statusCode": HTTPStatus.OK,
        "body": json.dumps(get_project_status_for_user(user_id, correlation_id))
    }


@utils.lambda_wrapper
@utils.api_error_handler
def get_project_status_for_external_user_api(event, context):
    """
    Lambda handler linked to API endpoint /v2/project-user-status
    """
    logger = event['logger']
    correlation_id = event['correlation_id']

    params = event['queryStringParameters']
    user_id = utils.validate_uuid(params['user_id'])
    logger.info('API call', extra={'user_id': user_id, 'correlation_id': correlation_id, 'event': event})
    return {
        "statusCode": HTTPStatus.OK,
        "body": json.dumps(get_project_status_for_user(user_id, correlation_id, anonymise_url=True))
    }
