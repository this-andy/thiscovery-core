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
                        status                         
                    from public.projects_projecttask task
                    where task.project_id = project.id
                    order by created
                    ) task_row
            ) as tasks
        from public.projects_project project
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
        status
      FROM 
        public.projects_project
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
    sql_where_clause = "WHERE id = %s "
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


def list_publicly_visible_projects(correlation_id):
    base_sql = '''
      SELECT 
        id, 
        name,
        short_name,
        created,
        modified,
        status
      FROM 
        public.projects_project p
      WHERE NOT EXISTS (
        SELECT id 
        FROM public.projects_projectgroupvisibility
        WHERE project_id = p.id
        )
      ORDER BY 
        created
    '''

    return execute_query(base_sql, None, correlation_id)


def list_user_visible_projects(user_uuid, correlation_id):
    base_sql = """
      SELECT 
        id, 
        name,
        short_name,
        created,
        modified,
        status
      FROM 
        public.projects_project p
      WHERE EXISTS (
        SELECT pgv.id 
        FROM public.projects_projectgroupvisibility pgv
        INNER JOIN projects_usergroup ug on pgv.user_group_id = ug.id
        INNER JOIN projects_usergroupmembership ugm on ug.id = ugm.user_group_id
       WHERE project_id = p.id 
       AND ugm.user_id = %s
      )"""

    return execute_query(base_sql, (user_uuid,), correlation_id)


def list_user_visibles(user_uuid, correlation_id):
    base_sql = """
      SELECT 
        *
      FROM public.projects_project p
      WHERE p.id = %s"""

    # return execute_query(base_sql, correlation_id)
    return execute_query(base_sql, (user_uuid,), correlation_id)


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
    result = list_user_visible_projects('04306e5c-b04f-4d2c-9e82-97fee2d135af','123')
    print(result)

    # print(list_projects_with_tasks(None))
    # print(json.dumps(list_projects(None)))
