from jinja2 import Template

import common.sql_templates as sql_t


def subquery(query):
    return f'(\n{query}\n)'


# region notification_process
SIGNUP_DETAILS_SELECT_SQL = '''
SELECT 
    p.id as project_id,
    p.name as project_name,
    pt.id as task_id,
    pt.description as task_name,
    tt.id as task_type_id,
    tt.name as task_type_name,
    u.crm_id
FROM 
    public.projects_project p
    JOIN projects_projecttask pt on p.id = pt.project_id
    JOIN projects_tasktype tt on pt.task_type_id = tt.id
    JOIN projects_usertask ut on pt.id = ut.project_task_id
    JOIN projects_userproject up on ut.user_project_id = up.id
    JOIN projects_user u on up.user_id = u.id
WHERE
    ut.id = %s
'''
# endregion


# region progress_process
external_system_id_by_name = """
    SELECT 
        id
    FROM
        public.projects_externalsystem
    WHERE
        name = (%s)
"""


project_task_id_subquery = sql_t.project_tasks_by_external_id.render(pt_id_alias='project_task_id', filter_by_external_system_id=True)


UPDATE_USER_TASK_PROGRESS_SQL = f'''
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


UPDATE_PROJECT_TASK_PROGRESS_SQL = f'''
    UPDATE public.projects_projecttask
    SET progress_info = (%s), progress_info_modified = (%s)
    WHERE id = 
        (
        {project_task_id_subquery}
        );
'''
# endregion


# region project
BASE_PROJECT_SELECT_SQL = '''
    SELECT row_to_json(project_row) 
    from (
        select 
            id, 
            name,
            short_name,
            description,
            project_page_url,
            created,
            modified,
            visibility,
            status,
            (
                select coalesce(json_agg(task_row), '[]'::json)
                from (
                    select 
                        id,
                        name,
                        short_name,
                        description,
                        task_page_url,
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


TASKS_BY_EXTERNAL_ID_SQL = sql_t.project_tasks_by_external_id.render(extra_columns=[
    'project_id',
    'task_type_id',
    'base_url',
    'external_system_id',
    'external_task_id',
    'es.short_name as task_provider_name',
])


TASK_INVITE_OR_REMIND_BASE = '''
    SELECT
        description as task_description,
        tt.short_name as task_type_name,
        p.short_name as project_short_name
    FROM public.projects_projecttask pt
    JOIN public.projects_project p on pt.project_id = p.id
    JOIN public.projects_tasktype tt on pt.task_type_id = tt.id
'''


TASKS_BY_USER_GROUP_ID_SQL = f'''
    {TASK_INVITE_OR_REMIND_BASE}
    JOIN public.projects_projecttaskgroupvisibility ptgv on pt.id = ptgv.project_task_id
    JOIN public.projects_usergroup ug on ptgv.user_group_id = ug.id
    WHERE ug.id = %s
'''


TASK_REMINDER_SQL = f'''
    {TASK_INVITE_OR_REMIND_BASE}
    WHERE pt.id = %s
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
        es.short_name as task_provider_name,
        user_specific_url,
        anonymise_url,
		tt.short_name as task_type_name
    FROM public.projects_projecttask pt
    JOIN public.projects_externalsystem es on pt.external_system_id = es.id
	JOIN public.projects_tasktype tt on pt.task_type_id = tt.id
    WHERE pt.id = %s
'''


UPDATE_PROJECT_TASK_SQL = '''
    UPDATE public.projects_projecttask
    SET progress_info = (%s), progress_info_modified = (%s)
    WHERE id = (%s);
'''


PROJECT_USER_SELECT_SQL_NON_DEMO_ONLY = sql_t.project_user_select_template.render()
PROJECT_USER_SELECT_SQL_DEMO_ONLY = sql_t.project_user_select_template.render(demo=True)


get_project_status_for_user_sql = {
    'sql0': """
        SELECT project_id
        FROM public.project_group_users
        WHERE user_id = %s
    """,

    'sql1': """
        SELECT project_id
        FROM public.project_testgroup_users
        WHERE user_id = %s
    """,

    'sql2': """
        SELECT project_task_id
        FROM public.projecttask_group_users
        WHERE user_id = %s
    """,

    'sql3': """
        SELECT project_task_id
        FROM public.projecttask_testgroup_users
        WHERE user_id = %s
    """,

    'sql4': """
        SELECT project_task_id, ut.id, ut.status, anon_project_specific_user_id, anon_user_task_id, user_task_url
        FROM public.projects_usertask ut
        JOIN public.projects_userproject up ON ut.user_project_id = up.id
        WHERE up.user_id = %s
    """,

    'sql5': """
        SELECT first_name, last_name, email
        FROM public.projects_user
        WHERE id = %s
    """,
}


GET_PROJECT_BY_PROJECT_TASK_ID_SQL = '''
    SELECT project_id 
    FROM public.projects_projecttask
    WHERE id = %s;
'''
# endregion


# region user
BASE_USER_SELECT_SQL = '''
    SELECT
        u.id,
        u.created,
        u.modified,
        u.email,
        u.title,
        u.first_name,
        u.last_name,
        u.country_code,
        u.auth0_id,
        u.crm_id,
        u.status,
        (
            SELECT EXISTS (
				SELECT 1 FROM projects_usergroupmembership ugm
				JOIN projects_usergroup ug ON ug.id = ugm.user_group_id
				WHERE ugm.user_id = u.id AND ug.demo = TRUE
			)
		) as has_demo_project,
		(
		    SELECT EXISTS (
				SELECT 1 FROM projects_usergroupmembership ugm
				JOIN projects_usergroup ug ON ug.id = ugm.user_group_id
				WHERE ugm.user_id = u.id AND ug.demo = FALSE
			)
		) as has_live_project
    FROM
        public.projects_user u
    '''


GET_USER_BY_ANON_PROJECT_SPECIFIC_USER_ID_SQL = f'''
    {BASE_USER_SELECT_SQL}
        JOIN public.projects_userproject as up on up.user_id = u.id
    WHERE
        up.anon_project_specific_user_id = (%s)
'''


GET_USER_BY_ANY_ANON_ID_SQL = f'''
    {BASE_USER_SELECT_SQL}
        JOIN public.projects_userproject as up on up.user_id = u.id
        JOIN public.projects_usertask as ut on ut.user_project_id = up.id
    WHERE
        up.anon_project_specific_user_id = (%s) OR
        ut.anon_user_task_id = (%s)
'''


CREATE_USER_SQL = '''
    INSERT INTO public.projects_user (
        id,
        created,
        modified,
        email,
        title,
        first_name,
        last_name,
        country_code,
        auth0_id,
        status
    ) VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s, %s );
'''
# endregion


# region user_external_account
CHECK_USER_ID_AND_EXTERNAL_ACCOUNT_SQL = '''
SELECT 
    id 
FROM public.projects_userexternalaccount
WHERE
    user_id = %s AND external_system_id = %s
'''

CREATE_USER_EXTERNAL_ACCOUNT_SQL = '''
    INSERT INTO public.projects_userexternalaccount (
        id,
        created,
        modified,
        external_system_id,
        user_id,
        external_user_id,
        status
    ) VALUES ( %s, %s, %s, %s, %s, %s, %s );
'''
# endregion


# region user_group
USER_GROUP_BASE_SELECT_SQL = '''
SELECT 
    id, 
    created, 
    modified, 
    name, 
    short_name, 
    url_code
FROM 
    public.projects_usergroup
'''


CREATE_USER_GROUP_SQL = '''
    INSERT INTO public.projects_usergroup (
        id, 
        created, 
        modified, 
        name, 
        short_name, 
        url_code
    ) VALUES ( %s, %s, %s, %s, %s, %s );
'''
# endregion


# region user_group_membership
SQL_USER = """
    SELECT id
    FROM public.projects_user
    WHERE id = %s
"""

SQL_USER_GROUP = """
    SELECT id
    FROM public.projects_usergroup
    WHERE id = %s
"""

SQL_USER_GROUP_MEMBERSHIP = """
    SELECT id
    FROM public.projects_usergroupmembership
    WHERE user_id = %s and user_group_id = %s
"""

SQL_USER_IDS_IN_USER_GROUP = """
    SELECT user_id
    FROM public.projects_usergroupmembership
    WHERE user_group_id = %s
"""

INSERT_USER_GROUP_MEMBERSHIP_SQL = '''
    INSERT INTO public.projects_usergroupmembership (
        id,
        created,
        modified,
        user_id,
        user_group_id
    ) VALUES ( %s, %s, %s, %s, %s );'''
# endregion


# region user_project
LIST_USER_PROJECTS_SQL = '''
    SELECT 
        id,
        user_id,
        project_id,
        created,
        modified,               
        status,
        anon_project_specific_user_id                
    FROM 
        public.projects_userproject
    WHERE user_id = %s
'''

GET_EXISTING_USER_PROJECT_ID_SQL = """
SELECT 
    id,
    anon_project_specific_user_id
FROM public.projects_userproject
WHERE 
    project_id = %s
    AND user_id = %s
"""

CREATE_USER_PROJECT_SQL = '''
    INSERT INTO public.projects_userproject (
        id,
        created,
        modified,
        user_id,
        project_id,
        status,
        anon_project_specific_user_id
    ) VALUES ( %s, %s, %s, %s, %s, %s, %s );
'''


LIST_USERS_BY_PROJECT_SQL = '''
    SELECT 
        up.anon_project_specific_user_id,
        up.user_id,
        u.email,
        u.first_name,
        u.last_name,
        up.project_id             
    FROM 
        public.projects_userproject up
    JOIN 
        public.projects_user u on up.user_id = u.id
    WHERE up.project_id = %s
'''
# endregion


# region user_task
ANON_USER_TASK_ID_2_ID_SQL = '''
    SELECT 
        ut.id, up.user_id              
    FROM 
        public.projects_usertask ut
    JOIN public.projects_userproject up on up.id = ut.user_project_id
    WHERE ut.anon_user_task_id = %s
'''

GET_USER_TASK_SQL = '''
    SELECT 
        ut.id,
        ut.user_project_id,
        ut.project_task_id,
        ut.created,
        ut.modified,               
        ut.status,
        ut.consented,
        ut.progress_info,
        up.user_id              
    FROM 
        public.projects_usertask ut
    JOIN projects_userproject up on ut.user_project_id = up.id
    WHERE ut.id = %s
'''

UPDATE_USER_TASK_PROGRESS_INFO_SQL = '''
    UPDATE public.projects_usertask
    SET progress_info = (%s)
    WHERE id = (%s);
'''

UPDATE_USER_TASK_STATUS = '''
    UPDATE 
        public.projects_usertask
    SET 
        status = (%s),
        modified = (%s)
    WHERE id = (%s);
'''

LIST_USER_TASKS_SQL = '''
    SELECT 
        up.user_id,
        ut.user_project_id,
        up.status as user_project_status,
        ut.project_task_id,
        pt.description as task_description,
        ut.id as user_task_id,
        ut.created,
        ut.modified,               
        ut.status,
        ut.consented,
        ut.anon_user_task_id,
        es.short_name as task_provider_name,
        ut.progress_info,
        pt.base_url,
        pt.external_task_id,
        pt.user_specific_url,
        ut.user_task_url,
        pt.anonymise_url,
        up.anon_project_specific_user_id
    FROM 
        public.projects_usertask ut
        inner join public.projects_projecttask pt on pt.id = ut.project_task_id
        inner join public.projects_externalsystem es on pt.external_system_id = es.id
        inner join public.projects_userproject up on up.id = ut.user_project_id
    WHERE up.user_id = %s
    ORDER BY ut.created
'''


CHECK_IF_USER_TASK_EXISTS_SQL = '''
SELECT 
    ut.id
FROM projects_usertask ut
    JOIN projects_userproject up on ut.user_project_id = up.id
WHERE
    up.user_id = %s
AND ut.project_task_id = %s
'''

CREATE_USER_TASK_SQL = '''
    INSERT INTO public.projects_usertask (
        id,
        created,
        modified,
        user_project_id,
        project_task_id,
        status,
        consented,
        anon_user_task_id,
        user_task_url
    ) VALUES ( %s, %s, %s, %s, %s, %s, %s, %s, %s );
'''

DELETE_USER_TASKS_FOR_PROJECT_TASK_SQL = '''
    DELETE FROM public.projects_usertask
    WHERE project_task_id = %s
'''
# endregion


# region entity_update
SAVE_ENTITY_UPDATE_SQL = '''
    INSERT INTO public.projects_entityupdate (
        id,
        created,
        modified,
        entity_name,
        entity_id,
        json_patch,
        json_reverse_patch
    ) VALUES ( %s, %s, %s, %s, %s, %s, %s);
'''

GET_ENTITY_UPDATES_FOR_ENTITY_SQL = '''
    SELECT
        id,
        created,
        modified,
        entity_name,
        entity_id,
        json_patch,
        json_reverse_patch
    FROM public.projects_entityupdate 
    WHERE entity_name = %s 
        AND entity_id = %s
    ORDER BY created
'''
# endregion


# region project task user groups
TEST_GROUP_USERS_FOR_PROJECT_TASK = '''
    SELECT u.id AS user_id
    FROM projects_projecttask pt
        JOIN projects_usergroup ug ON ug.id = pt.testing_group_id
        JOIN projects_usergroupmembership ugm ON ug.id = ugm.user_group_id
        JOIN projects_user u ON ugm.user_id = u.id
    WHERE pt.id = %s
'''


USER_GROUP_FOR_PROJECT_TASK = '''
    SELECT user_id
    FROM public.projecttask_group_users
    WHERE project_task_id = %s
'''
# endregion
