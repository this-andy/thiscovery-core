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
from common.cochrane import get_progress
from common.utilities import get_correlation_id, get_logger
from project import update_project_task_progress_info, get_project_task_by_external_task_id
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

    logger = get_logger()
    correlation_id = get_correlation_id(event)
    progress_dict = get_progress()
    progress_info_modified = progress_dict['daterun']

    progress_by_task = sort_progress_by_task(progress_dict)
    updated_project_tasks = 0
    updated_user_tasks = 0
    for k, v in progress_by_task.items():
        try:
            pt_id = get_project_task_by_external_task_id(k, correlation_id)[0]
            project_task_assessments = 0
            for record in v:
                user_task_assessments = record['count']
                target_user_task = filter_user_tasks_by_project_task_id(record['uuid'], pt_id, correlation_id)
                user_task_progress_info_dict = {'total assessments': user_task_assessments}
                user_task_id = target_user_task['user_task_id']
                logger.info('About to update progress info of user task', extra={'user_task_id': user_task_id, 'progress_info': user_task_progress_info_dict,
                                                                                 'correlation_id': correlation_id, 'event': event})
                updated_user_tasks += update_user_task_progress_info(user_task_id, user_task_progress_info_dict, correlation_id)
                project_task_assessments += user_task_assessments
            project_task_progress_info_dict = {'total assessments': project_task_assessments}
            logger.info('About to update progress info of project task', extra={'project_task_id': pt_id, 'progress_info': project_task_progress_info_dict,
                                                                                'correlation_id': correlation_id, 'event': event})
            updated_project_tasks += update_project_task_progress_info(pt_id, project_task_progress_info_dict, progress_info_modified, correlation_id)
        except IndexError as err:
            logger.error(f'Could not find any project tasks matching external task id {k}')

    return {'updated_project_tasks': updated_project_tasks, 'updated_user_tasks': updated_user_tasks}


if __name__ == "__main__":
    update_cochrane_progress(None, None)