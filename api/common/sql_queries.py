from jinja2 import Template

# region project
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

BASE_PROJECT_SELECT_SQL = '''
    SELECT row_to_json(project_row) 
    from (
        select 
            id, 
            name,
            short_name,
            created,
            modified,
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
                        visibility,
                        external_system_id,                       
                        external_task_id, 
                        base_url,                      
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

TASKS_BY_EXTERNAL_ID_SQL = '''
            SELECT
                pt.id,
                project_id,
                task_type_id,
                base_url,
                external_system_id,
                external_task_id,
                es.short_name as task_provider_name
            FROM public.projects_projecttask pt
            JOIN projects_externalsystem es on pt.external_system_id = es.id
            WHERE external_task_id = (%s)
    '''

LIST_PROJECTS_SQL = '''
      SELECT 
        id, 
        name,
        short_name,
        created,
        modified,
        visibility,
        status
      FROM 
        public.projects_project
      WHERE projects_project.status != 'planned'
      ORDER BY 
        created
    '''

GET_PROJECT_TASK_SQL = '''
        SELECT
            pt.id as project_task_id,
            project_id,
            task_type_id,
            base_url,
            external_system_id,
            external_task_id,
            progress_info,
            progress_info_modified,
            es.short_name as task_provider_name
        FROM public.projects_projecttask pt
        JOIN projects_externalsystem es on pt.external_system_id = es.id
        WHERE pt.id = %s
    '''

UPDATE_PROJECT_TASK_PROGRESS_INFO_SQL = '''
                UPDATE public.projects_projecttask
                SET progress_info = (%s), progress_info_modified = (%s)
                WHERE id = (%s);
            '''

PROJECT_USER_SELECT_SQL = '''
    SELECT row_to_json(project_row) 
    from (
        select 
            id, 
            short_name,
            visibility,
            status,
            FALSE as project_is_visible,
            (
                select coalesce(json_agg(task_row), '[]'::json)
                from (
                    select 
                        task.id,
                        description,
                        signup_status,
                        visibility,   
                        external_task_id,
                        base_url as url,                    
                        status,
                        es.short_name as task_provider_name,
                        FALSE as task_is_visible,
                        FALSE as user_is_signedup,
                        FALSE as signup_available,
                        null as user_task_status
                    from public.projects_projecttask task
                    join public.projects_externalsystem es on task.external_system_id = es.id
                    where task.project_id = project.id
                        AND task.status != 'planned'                   
                    order by task.created
                    ) task_row
            ) as tasks
        from public.projects_project project
        where project.status != 'planned'
        order by created
        ) project_row
    '''


get_project_status_for_user_template = {
    'sql0': Template("""
        SELECT project_id, project_name, group_id, group_name, user_id, email {%- if extra_columns %}, {{ extra_columns|join(', ') }}{% endif %}
        FROM public.project_group_users
        WHERE {{ filter }} = %s
    """),

    'sql1': Template("""
        SELECT project_id, project_name, testing_group_id, group_name, user_id, email {%- if extra_columns %}, {{ extra_columns|join(', ') }}{% endif %}
        FROM public.project_testgroup_users
        WHERE {{ filter }} = %s
    """),

    'sql2': Template("""
        SELECT project_task_id, description, group_id, group_name, user_id, email {%- if extra_columns %}, {{ extra_columns|join(', ') }}{% endif %}
        FROM public.projecttask_group_users
        WHERE {{ filter }} = %s
    """),

    'sql3': Template("""
        SELECT project_task_id, description, testing_group_id, group_name, user_id, email {%- if extra_columns %}, {{ extra_columns|join(', ') }}{% endif %}
        FROM public.projecttask_testgroup_users
        WHERE {{ filter }} = %s
    """),

    'sql4': Template("""
        SELECT project_task_id, ut.id, ut.status {%- if extra_columns %}, {{ extra_columns|join(', ') }}{% endif %}
        FROM public.projects_usertask ut
        JOIN public.projects_userproject up ON ut.user_project_id = up.id
        WHERE {{ filter }} = %s
    """),
}

get_project_status_for_user_sql = {k: v.render(filter='user_id') for k, v in get_project_status_for_user_template.items()}
get_project_status_for_user_sql['sql4'] = get_project_status_for_user_template['sql4'].render(filter='up.user_id')

get_project_status_for_external_user_sql = {k: v.render(extra_columns=['ext_user_project_id'], filter='ext_user_project_id') for k, v in
                                            get_project_status_for_user_template.items()}
get_project_status_for_external_user_sql['sql4'] = get_project_status_for_user_template['sql4'].render(
    extra_columns=['up.ext_user_project_id as ext_user_project_id', 'ut.ext_user_task_id as ext_user_task_id'],
    filter='ext_user_project_id')
# endregion
