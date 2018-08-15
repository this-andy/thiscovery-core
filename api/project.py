import json
import sys
from api.pg_utilities import execute_query, _jsonize_sql, _get_json_from_tuples
from api.utilities import get_correlation_id, get_logger, error_as_response_body


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

    return execute_query(base_sql, correlation_id)


def list_projects_with_tasks(correlation_id):
    base_sql = '''
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
                            status                         
                        from public.projects_task task
                        where task.project_id = project.id
                        order by created
                        ) task_row
                ) as tasks
            from public.projects_project project
            order by created
            ) project_row
    '''

    result = execute_query(base_sql, correlation_id, True, False)

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


if __name__ == "__main__":
    result = list_projects_api(None, None)
    result_status = result['statusCode']
    result_json = json.loads(result['body'])
    print(result)

    # print(list_projects_with_tasks(None))
    # print(json.dumps(list_projects(None)))
