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
import common.sql_queries as sql_q

from common.cochrane import get_progress
from thiscovery_lib.utilities import get_correlation_id, get_logger


@pg_utils.db_connection_handler
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

    logger = get_logger()
    correlation_id = get_correlation_id(event)
    external_system_name = 'Cochrane Crowd'
    try:
        external_system_id = pg_utils.execute_query(sql_q.external_system_id_by_name, [external_system_name])[0]['id']
    except TypeError as err:
        logger.error(f'Could not find an external system named "{external_system_name}"')
        raise err

    progress_dict = get_progress()
    progress_info_modified = progress_dict['daterun']

    progress_by_task = sort_progress_by_task(progress_dict)
    user_tasks_sql_queries, project_tasks_sql_queries = list(), list()
    for external_task_id, v in progress_by_task.items():
        logger.info(f'Working on task {external_task_id}')
        project_task_assessments = 0

        for record in v:
            user_id = record['uuid']
            user_task_assessments = record['count']
            user_task_progress_info_json = json.dumps({'total assessments': user_task_assessments})
            user_tasks_sql_queries.append((sql_q.UPDATE_USER_TASK_PROGRESS_SQL,
                                           (user_task_progress_info_json, user_id, external_task_id, external_system_id)))
            project_task_assessments += user_task_assessments

        project_task_progress_info_json = json.dumps({'total assessments': project_task_assessments})
        project_tasks_sql_queries.append((sql_q.UPDATE_PROJECT_TASK_PROGRESS_SQL,
                                          (project_task_progress_info_json, progress_info_modified, external_task_id, external_system_id)))

    multiple_sql_queries = [x[0] for x in user_tasks_sql_queries] + [x[0] for x in project_tasks_sql_queries]
    multiple_params = [x[1] for x in user_tasks_sql_queries] + [x[1] for x in project_tasks_sql_queries]
    updated_rows = pg_utils.execute_non_query_multiple(multiple_sql_queries, multiple_params, correlation_id)

    assert len(updated_rows) == len(project_tasks_sql_queries) + len(user_tasks_sql_queries), 'Number of updated database rows does not match number of ' \
                                                                                              'executed sql queries'

    return {'updated_project_tasks': len(project_tasks_sql_queries), 'updated_user_tasks': len(user_tasks_sql_queries)}
