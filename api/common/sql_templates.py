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
        external_task_id = (%s)
    """
)






