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
        Converts task ids in Cochrane progress report from integer to string. Sorts Cochrane progress report by tasks.
        Returns a sorted dictionary in the format:
        {
        "4000": [{"count":6,"uuid":"2a328477-c47e-4758-a43f-2db537983438"}, {"count":7,"uuid":"2ef570b4-c0d5-4de9-8198-f8287942e4e4"}],
        "5500": [{"count":5,"uuid":"2a328477-c47e-4758-a43f-2db537983438"}, {"count":19,"uuid":"2ef570b4-c0d5-4de9-8198-f8287942e4e4"}]
        }
        """
        tasks_progress = dict()
        for r in progress_dict_['records']:
            r['task'] = str(r['task'])
            if r['task'] in tasks_progress.keys():
                tasks_progress[r['task']].append({'count': r['count'], 'uuid': r['uuid']})
            else:
                tasks_progress[r['task']] = [{'count': r['count'], 'uuid': r['uuid']}]
        return tasks_progress

    start_time = get_start_time()
    logger = get_logger()
    correlation_id = get_correlation_id(event)

    progress_dict = get_progress()
    progress_info_modified = progress_dict['daterun']

    progress_by_task = sort_progress_by_task(progress_dict)
    # updated_project_tasks = 0
    # updated_user_tasks = 0
    logger.info('Execution time before for loop', extra={'progress items processed': progress_by_task, 'elapsed_ms': get_elapsed_ms(start_time)})
    user_tasks_sql_queries, project_tasks_sql_queries = list(), list()
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
            user_tasks_sql_queries.append((ut_sql, (user_task_progress_info_json, user_id, external_task_id)))

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
        project_tasks_sql_queries.append((pt_sql, (project_task_progress_info_json, progress_info_modified, external_task_id)))

    multiple_sql_queries = [x[0] for x in user_tasks_sql_queries] + [x[0] for x in project_tasks_sql_queries]
    multiple_params = [x[1] for x in user_tasks_sql_queries] + [x[1] for x in project_tasks_sql_queries]
    updated_rows = pg_utils.execute_non_query_multiple(multiple_sql_queries, multiple_params, correlation_id)

    assert len(updated_rows) == len(project_tasks_sql_queries) + len(user_tasks_sql_queries), 'Number of updated database rows does not match number of ' \
                                                                                              'executed sql queries'

    logger.info('Total execution time', extra={'progress items processed': progress_by_task, 'elapsed_ms': get_elapsed_ms(start_time)})
    return {'updated_project_tasks': len(project_tasks_sql_queries), 'updated_user_tasks': len(user_tasks_sql_queries)}
