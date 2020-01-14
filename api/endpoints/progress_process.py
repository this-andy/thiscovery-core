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

import common.pg_utilities as pg_utils
import project as p
from common.cochrane import get_progress
from common.utilities import get_correlation_id, get_logger, ObjectDoesNotExistError, get_start_time, get_elapsed_ms
from user_task import filter_user_tasks_by_project_task_id, update_user_task_progress_info


def update_cochrane_progress(event, context):
    """
    AWS lambda handler to update progress of task hosted by Cochrane Crowd
    """

    def sort_progress_by_task(progress_dict_):
        """
        Sorts Cochrane progress report by tasks. Returns a sorted dictionary in the format:
        {
        4000: [{"count":6,"uuid":"2a328477-c47e-4758-a43f-2db537983438"}, {"count":7,"uuid":"2ef570b4-c0d5-4de9-8198-f8287942e4e4"}],
        5500: [{"count":5,"uuid":"2a328477-c47e-4758-a43f-2db537983438"}, {"count":19,"uuid":"2ef570b4-c0d5-4de9-8198-f8287942e4e4"}]
        }
        """
        tasks_progress = dict()
        for r in progress_dict_['records']:
            if r['task'] in tasks_progress.keys():
                tasks_progress[r['task']].append({'count': r['count'], 'uuid': r['uuid']})
            else:
                tasks_progress[r['task']] = [{'count': r['count'], 'uuid': r['uuid']}]
        return tasks_progress

    start_time = get_start_time()
    logger = get_logger()
    correlation_id = get_correlation_id(event)

    # optional base_url queryStringParameter so that tests can always point to mock API
    params = event['queryStringParameters']
    api_url = params.get('api_url')

    if api_url:
        progress_dict = get_progress(api_url=api_url)
    else:
        progress_dict = get_progress()
    progress_info_modified = progress_dict['daterun']

    progress_by_task = sort_progress_by_task(progress_dict)
    updated_project_tasks = 0
    updated_user_tasks = 0
    logger.info('Execution time before for loop', extra={'progress items processed': progress_by_task, 'elapsed_ms': get_elapsed_ms(start_time)})
    sql_queries = []
    for external_task_id, v in progress_by_task.items():
        logger.info(f'Working on task {external_task_id}')
        project_task_assessments = 0
        for record in v:
            user_id = record['uuid']
            user_task_assessments = record['count']
            user_task_progress_info_json = json.dumps({'total assessments': user_task_assessments})

            project_task_id_subquery = '''
                    SELECT
                    pt.id as project_task_id
                    FROM
                    public.projects_projecttask pt
                    JOIN projects_externalsystem es on pt.external_system_id = es.id
                    WHERE external_task_id = (%s)
            '''

            ut_sql = f'''
                UPDATE public.projects_usertask
                SET progress_info = (%s)
                WHERE id = 
                (
                    SELECT 
                        ut.id as user_task_id 
                    FROM 
                        public.projects_usertask ut 
                        JOIN public.projects_projecttask pt on pt.id = ut.project_task_id
                        JOIN public.projects_userproject up on up.id = ut.user_project_id
                    WHERE up.user_id = (%s) AND ut.project_task_id = 
                         (
                         {project_task_id_subquery}
                         )
                    ORDER BY ut.created
                );
            '''

            # updated_user_tasks += pg_utils.execute_non_query(ut_sql, (user_task_progress_info_json, user_id, external_task_id), correlation_id)
            sql_queries.append((ut_sql, (user_task_progress_info_json, user_id, external_task_id)))

            project_task_assessments += user_task_assessments

        project_task_progress_info_json = json.dumps({'total assessments': project_task_assessments})

        pt_sql = f'''
                UPDATE public.projects_projecttask
                SET progress_info = (%s), progress_info_modified = (%s)
                WHERE id = 
                    (
                    {project_task_id_subquery}
                    );
            '''

        # updated_project_tasks += pg_utils.execute_non_query(pt_sql, (project_task_progress_info_json, progress_info_modified, external_task_id), correlation_id)
        sql_queries.append((pt_sql, (project_task_progress_info_json, progress_info_modified, external_task_id)))


    logger.info('Total execution time', extra={'progress items processed': progress_by_task, 'elapsed_ms': get_elapsed_ms(start_time)})
    return {'updated_project_tasks': updated_project_tasks, 'updated_user_tasks': updated_user_tasks}


# function below is not used anywhere and can be delete. Leaving it here for now in case the approach of executing queries in batch doesn't work
def update_cochrane_progress_one_by_one(event, context):
    """
    AWS lambda handler to update progress of task hosted by Cochrane Crowd. This function executes SQL queries one by one, which facilates error
    handling at the expense of performance.
    """

    def sort_progress_by_task(progress_dict_):
        """
        Sorts Cochrane progress report by tasks. Returns a sorted dictionary in the format:
        {
        4000: [{"count":6,"uuid":"2a328477-c47e-4758-a43f-2db537983438"}, {"count":7,"uuid":"2ef570b4-c0d5-4de9-8198-f8287942e4e4"}],
        5500: [{"count":5,"uuid":"2a328477-c47e-4758-a43f-2db537983438"}, {"count":19,"uuid":"2ef570b4-c0d5-4de9-8198-f8287942e4e4"}]
        }
        """
        tasks_progress = dict()
        for r in progress_dict_['records']:
            if r['task'] in tasks_progress.keys():
                tasks_progress[r['task']].append({'count': r['count'], 'uuid': r['uuid']})
            else:
                tasks_progress[r['task']] = [{'count': r['count'], 'uuid': r['uuid']}]
        return tasks_progress

    start_time = get_start_time()
    logger = get_logger()
    correlation_id = get_correlation_id(event)

    # optional base_url queryStringParameter so that tests can always point to mock API
    params = event['queryStringParameters']
    api_url = params.get('api_url')

    if api_url:
        progress_dict = get_progress(api_url=api_url)
    else:
        progress_dict = get_progress()
    progress_info_modified = progress_dict['daterun']

    progress_by_task = sort_progress_by_task(progress_dict)
    updated_project_tasks = 0
    updated_user_tasks = 0
    logger.info('Execution time before for loop', extra={'progress items processed': progress_by_task, 'elapsed_ms': get_elapsed_ms(start_time)})
    for k, v in progress_by_task.items():
        logger.info(f'Working on task {k}')

        try:
            pt_id = p.get_project_task_by_external_task_id(k, correlation_id)[0]
        except IndexError:
            raise ObjectDoesNotExistError(f'Could not find any project tasks matching external task id {k}')

        project_task_assessments = 0
        for record in v:
            user_task_assessments = record['count']
            target_user_task = filter_user_tasks_by_project_task_id(record['uuid'], pt_id, correlation_id)
            user_task_progress_info_dict = {'total assessments': user_task_assessments}
            try:
                user_task_id = target_user_task['user_task_id']
            except TypeError:
                raise ObjectDoesNotExistError(f"User {record['uuid']} does not have a task associated with project {pt_id}")

            logger.info('About to update progress info of user task', extra={'user_task_id': user_task_id, 'progress_info': user_task_progress_info_dict,
                                                                             'correlation_id': correlation_id, 'event': event})
            updated_user_tasks += update_user_task_progress_info(user_task_id, user_task_progress_info_dict, correlation_id)
            project_task_assessments += user_task_assessments
        project_task_progress_info_dict = {'total assessments': project_task_assessments}
        logger.info('About to update progress info of project task', extra={'project_task_id': pt_id, 'progress_info': project_task_progress_info_dict,
                                                                            'correlation_id': correlation_id, 'event': event})
        updated_project_tasks += p.update_project_task_progress_info(pt_id, project_task_progress_info_dict, progress_info_modified, correlation_id)

    logger.info('Total execution time', extra={'progress items processed': progress_by_task, 'elapsed_ms': get_elapsed_ms(start_time)})
    return {'updated_project_tasks': updated_project_tasks, 'updated_user_tasks': updated_user_tasks}


if __name__ == "__main__":
    update_cochrane_progress(None, None)