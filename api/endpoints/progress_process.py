import uuid
import json
from http import HTTPStatus
from psycopg2.extras import Json

if 'api.endpoints' in __name__:
    from .common.cochrane import get_progress
    from .common.utilities import get_correlation_id
    from .project import update_project_task_progress_info, get_project_task_by_external_task_id
    from .user_task import filter_user_tasks_by_project_task_id, update_user_task_progress_info
else:
    from common.cochrane import get_progress
    from common.utilities import get_correlation_id
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

    correlation_id = get_correlation_id(event)
    progress_dict = get_progress()
    progress_info_modified = progress_dict['daterun']

    progress_by_task = sort_progress_by_task(progress_dict)
    updated_project_tasks = 0
    updated_user_tasks = 0
    for k, v in progress_by_task.items():
        pt_id = get_project_task_by_external_task_id(k, correlation_id)[0]
        project_task_assessments = 0
        for record in v:
            user_task_assessments = record['count']
            target_user_task = filter_user_tasks_by_project_task_id(record['uuid'], pt_id, correlation_id)
            user_task_progress_info_dict = {'total assessments': user_task_assessments}
            updated_user_tasks += update_user_task_progress_info(target_user_task['user_task_id'], user_task_progress_info_dict, correlation_id)
            project_task_assessments += user_task_assessments
        project_task_progress_info_dict = {'total assessments': project_task_assessments}
        updated_project_tasks += update_project_task_progress_info(pt_id, project_task_progress_info_dict, progress_info_modified, correlation_id)

    return {'updated_project_tasks': updated_project_tasks, 'updated_user_tasks': updated_user_tasks}


if __name__ == "__main__":
    update_cochrane_progress(None, None)