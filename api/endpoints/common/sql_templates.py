from jinja2 import Template


project_tasks_by_external_id = Template(
    """
    SELECT
        pt.id {% if pt_id_alias %} as {{ pt_id_alias }} {% endif %} 
        {%- if extra_columns %}, {{ extra_columns|join(', ') }}{% endif %}
    FROM
        public.projects_projecttask pt
        JOIN projects_externalsystem es on pt.external_system_id = es.id
    WHERE 
        external_task_id = (%s) {%- if filter_by_external_system_id %} AND pt.external_system_id = (%s) {%- endif %}
    """
)


project_user_select_template = Template(
    '''
    SELECT row_to_json(project_row) 
    FROM (
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
                        es.display_method as display_method,
                        FALSE as task_is_visible,
                        FALSE as user_is_signedup,
                        FALSE as signup_available,
                        null as user_task_status,
                        user_specific_url,
                        anonymise_url,
                        tt.short_name as task_type_name
                    from public.projects_projecttask task
                    join public.projects_externalsystem es on task.external_system_id = es.id
                    join public.projects_tasktype tt on task.task_type_id = tt.id
                    where task.project_id = project.id
                        AND task.status != 'planned'                   
                    order by task.created
                    ) task_row
            ) as tasks
    FROM public.projects_project project
    WHERE project.status != 'planned' AND 
        {% if demo %} 
            project.demo = TRUE 
        {% else %} 
            COALESCE(project.demo, FALSE) = FALSE 
        {% endif %} 
    ORDER BY created
    ) project_row
    '''
)
