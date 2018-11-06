import json
from api.pg_utilities import execute_query
from api.utilities import get_correlation_id, get_logger, error_as_response_body, ObjectDoesNotExistError


BASE_PROJECT_SELECT_SQL = '''
    SELECT row_to_json(project_row) 
    from (
        select 
            id, 
            name,
            short_name,
            created,
            modified,
            website_highlight,
            visibility,
            status,
            (
                select coalesce(json_agg(task_row), '[]'::json)
                from (
                    select 
                        id,
                        description,
                        created,
                        modified,
                        task_type_id,
                        earliest_start_date,
                        closing_date,
                        signup_status,
                        website_highlight,
                        visibility,                       
                        status                         
                    from public.projects_projecttask task
                    where task.project_id = project.id
                        AND task.status != 'planned'
                    order by created
                    ) task_row
            ) as tasks
        from public.projects_project project
        where project.status != 'planned'
        order by created
        ) project_row
'''

MINIMAL_PROJECT_SELECT_SQL = '''
    SELECT row_to_json(project_row) 
    from (
        select 
            id, 
            short_name,
            visibility,
            status,
            (
                select coalesce(json_agg(task_row), '[]'::json)
                from (
                    select 
                        id,
                        description,
                        signup_status,
                        visibility,                       
                        status                         
                    from public.projects_projecttask task
                    where task.project_id = project.id
                        AND task.status != 'planned'
                    order by created
                    ) task_row
            ) as tasks
        from public.projects_project project
        where project.status != 'planned'
        order by created
        ) project_row
'''


def list_projects(correlation_id):
    base_sql = '''
      SELECT 
        id, 
        name,
        short_name,
        created,
        modified,
        website_highlight,
        visibility,
        status
      FROM 
        public.projects_project
      WHERE projects_project.status != 'planned'
      ORDER BY 
        created
    '''

    return execute_query(base_sql, None, correlation_id)


def list_projects_with_tasks(correlation_id):

    result = execute_query(BASE_PROJECT_SELECT_SQL, None, correlation_id, True, False)

    return result


def list_projects_api(event, context):
    logger = get_logger()
    correlation_id = None

    try:
        correlation_id = get_correlation_id(event)
        logger.info('API call', extra={'correlation_id': correlation_id, 'event': event})
        response = {
            "statusCode": 200,
            "body": json.dumps(list_projects_with_tasks(correlation_id))
        }

    except Exception as ex:
        errorMsg = ex.args[0]
        logger.error(errorMsg, extra={'correlation_id': correlation_id})
        response = {"statusCode": 500, "body": error_as_response_body(errorMsg, correlation_id)}

    logger.info('API response', extra={'response': response, 'correlation_id': correlation_id})
    return response


def get_project_with_tasks(project_uuid, correlation_id):
    # take base sql query and insert a where clause to get specified project
    sql_where_clause = " AND id = %s "
    # put where clause before final order by
    order_by_index = BASE_PROJECT_SELECT_SQL.rfind('order by')
    sql = BASE_PROJECT_SELECT_SQL[:order_by_index] + sql_where_clause + BASE_PROJECT_SELECT_SQL[order_by_index:]

    result = execute_query(sql, (str(project_uuid),), correlation_id, True, False)

    return result


def get_project_api(event, context):
    logger = get_logger()
    correlation_id = None

    try:
        correlation_id = get_correlation_id(event)
        project_id = event['pathParameters']['id']
        logger.info('API call', extra={'project_id': project_id, 'correlation_id': correlation_id, 'event': event})

        result = get_project_with_tasks(project_id, correlation_id)

        if len(result) > 0:
            response = {"statusCode": 200, "body": json.dumps(result)}
        else:
            errorjson = {'project_id': project_id, 'correlation_id': str(correlation_id)}
            raise ObjectDoesNotExistError('project does not exist', errorjson)

    except ObjectDoesNotExistError as err:
        response = {"statusCode": 404, "body": err.as_response_body()}

    except Exception as ex:
        errorMsg = ex.args[0]
        logger.error(errorMsg, extra={'correlation_id': correlation_id})
        response = {"statusCode": 500, "body": error_as_response_body(errorMsg, correlation_id)}

    logger.info('API response', extra={'response': response, 'correlation_id': correlation_id})
    return response

PROJECT_USER_SELECT_SQL = '''
    SELECT row_to_json(project_row) 
    from (
        select 
            id, 
            short_name,
            visibility,
            status,
            FALSE as is_visible,
            (
                select coalesce(json_agg(task_row), '[]'::json)
                from (
                    select 
                        id,
                        description,
                        signup_status,
                        visibility,                       
                        status,
                        FALSE as is_visible,
                        FALSE as is_signedup,
                        FALSE as sign_up_available,
                        null as user_task_status
                    from public.projects_projecttask task
                    where task.project_id = project.id
                        AND task.status != 'planned'
                    order by created
                    ) task_row
            ) as tasks
        from public.projects_project project
        where project.status != 'planned'
        order by created
        ) project_row
    '''


def dict_from_dataset(dataset, key_name):
    dataset_as_dict = {}
    for datarow in dataset:
        dataset_as_dict[datarow[key_name]] = datarow
    return dataset_as_dict


def get_project_status_for_user(user_id, correlation_id):

    project_list = execute_query(PROJECT_USER_SELECT_SQL, None, correlation_id, True, False)

    sql = """
        SELECT project_id, project_name, group_id, group_name, user_id, email
        FROM public.project_group_users
        WHERE user_id = %s
    """
    project_group_users = execute_query(sql, (str(user_id),), correlation_id)
    project_group_users_dict = dict_from_dataset(project_group_users, 'project_id')

    sql = """
        SELECT project_id, project_name, testing_group_id, group_name, user_id, email
        FROM public.project_testgroup_users
        WHERE user_id = %s
    """
    project_testgroup_users = execute_query(sql, (str(user_id),), correlation_id)
    project_testgroup_users_dict = dict_from_dataset(project_testgroup_users, 'project_id')

    sql = """
        SELECT project_task_id, description, group_id, group_name, user_id, email
	    FROM public.projecttask_group_users
        WHERE user_id = %s
    """
    projecttask_group_users = execute_query(sql, (str(user_id),), correlation_id)
    projecttask_group_users_dict = dict_from_dataset(projecttask_group_users,'project_task_id')

    sql = """
        SELECT project_task_id, description, testing_group_id, group_name, user_id, email
        FROM public.projecttask_testgroup_users
        WHERE user_id = %s
    """
    projecttask_testgroup_users = execute_query(sql, (str(user_id),), correlation_id)
    projecttask_testgroup_users_dict = dict_from_dataset(projecttask_testgroup_users,'project_task_id')

    sql = """
        SELECT project_task_id, ut.status
	    FROM public.projects_usertask ut
	    JOIN public.projects_userproject up ON ut.user_project_id = up.id
        WHERE up.user_id = %s
	"""
    projects_usertasks = execute_query(sql, (str(user_id),), correlation_id)
    projects_usertasks_dict = dict_from_dataset(projects_usertasks,'project_task_id')

    # now add calculated attributes to returned json...

    for project in project_list:
        project_id = project['id']
        project['is_visible'] = \
            ((project['status'] == 'testing') and (project_testgroup_users_dict.get(project_id) is not None)) \
            or ((project['status'] != 'testing') and \
                ((project['visibility'] == 'public') or \
                (project_group_users_dict.get(project_id) is not None)))
        for task in project['tasks']:
            task_id = task['id']
            task['is_visible'] = \
                project['is_visible'] and (
                    (task['visibility'] == 'public') \
                    or ((task['status'] == 'testing') and (projecttask_testgroup_users_dict.get(task_id) is not None)) \
                    or ((task['status'] != 'testing') and (projecttask_group_users_dict.get(task_id) is not None)))
            task['is_signedup'] = projects_usertasks_dict.get(task_id) is not None
            task['sign_up_available'] = \
                (task['is_visible'] and (task['status'] == 'active') and not task['is_signedup'] and (task['signup_status'] == 'open')) \
                or (task['is_visible'] and (task['status'] == 'testing') and not task['is_signedup'])
            if task['is_signedup']:
                task['user_task_status'] = projects_usertasks_dict[task_id]['status']

    return project_list


def get_project_status_for_user_api(event, context):
    logger = get_logger()
    correlation_id = None

    try:
        params = event['queryStringParameters']
        user_id = params['user_id']  # all public id are uuids
        correlation_id = get_correlation_id(event)
        logger.info('API call', extra={'user_id': user_id, 'correlation_id': correlation_id, 'event': event})
        response = {
            "statusCode": 200,
            "body": json.dumps(get_project_status_for_user(user_id, correlation_id))
        }

    except Exception as ex:
        errorMsg = ex.args[0]
        logger.error(errorMsg, extra={'correlation_id': correlation_id})
        response = {"statusCode": 500, "body": error_as_response_body(errorMsg, correlation_id)}

    logger.info('API response', extra={'response': response, 'correlation_id': correlation_id})
    return response



if __name__ == "__main__":

    # result = get_project_with_tasks('21c0779a-5fc2-4b72-8a88-0ba31456b562',None)

    # pp = {'id': "0c137d9d-e087-448b-ba8d-24141b6ceecd"}
    # ev = {'pathParameters': pp}
    # result = get_project_api(ev, None)

    # result = list_projects_api(None, None)
    # result_status = result['statusCode']
    # result_json = json.loads(result['body'])

    # result = list_publicly_visible_projects('123')
    # j "04306e5c-b04f-4d2c-9e82-97fee2d135af"
    # d "26ee974a-08de-4a89-a85e-bcdabc7d9944"
    # s "6b78f0fc-9266-40fb-a212-b06889a6811d"
    # a "a5634be4-af2a-4d4a-a282-663e8c816507"
    # result = list_user_visible_projects("6b78f0fc-9266-40fb-a212-b06889a6811d",'123')
    qsp = {'user_id': "851f7b34-f76c-49de-a382-7e4089b744e2"}
    ev = {'queryStringParameters': qsp}
    result = get_project_status_for_user_api(ev, None)
    print (result)
    # if len(result) == 0:
    #     print(result)
    # else:
    #     for item in result:
    #         print(item)

    # print(list_projects_with_tasks(None))
    # print(json.dumps(list_projects(None)))
