from api.pg_utilities import execute_query


def project_testgroup_users():
    base_sql = '''
      SELECT 
        p.id AS project_id, 
        p.short_name AS project_name,
        p.testing_group_id,
        ug.short_name AS group_name,
        u.id AS user_id,
        u.email
      FROM 
        public.projects_project p
      JOIN public.projects_usergroup ug on ug.id = p.testing_group_id
      JOIN projects_usergroupmembership ugm ON ug.id = ugm.user_group_id
      JOIN projects_user u ON ugm.user_id = u.id  
    '''

    return execute_query(base_sql, None, 'dummy-id')


def project_task_testgroup_users():
    base_sql = '''
      SELECT 
        pt.id AS project_task_id, 
        pt.description,
        pt.testing_group_id,
        ug.short_name AS group_name,
        u.id AS user_id,
        u.email
      FROM 
        public.projects_projecttask pt
      JOIN public.projects_usergroup ug on ug.id = pt.testing_group_id
      JOIN projects_usergroupmembership ugm ON ug.id = ugm.user_group_id
      JOIN projects_user u ON ugm.user_id = u.id  
    '''

    return execute_query(base_sql, None, 'dummy-id')


def project_group_users():
    # note that this query will produce duplicate project/user combinations where there are multiple groups connecting the two
    # we don't care about this as all that matters is the presence or absence from the dataset.
    base_sql = """
      SELECT 
        p.id AS project_id, 
        p.short_name AS project_name,
        ug.id AS group_id,
        ug.short_name AS group_name,
        u.id AS user_id,
        u.email
      FROM 
        public.projects_project p
      JOIN projects_projectgroupvisibility pgv ON p.id = pgv.project_id
      JOIN projects_usergroup ug on pgv.user_group_id = ug.id
      JOIN projects_usergroupmembership ugm on ug.id = ugm.user_group_id
      JOIN projects_user u ON ugm.user_id = u.id  
    """

    return execute_query(base_sql, None, 'dummy-id')


def project_task_group_users():
    # note that this query will produce duplicate project/user combinations where there are multiple groups connecting the two
    # we don't care about this as all that matters is the presence or absence from the dataset.

    base_sql = """
      SELECT 
        pt.id AS project_task_id, 
        pt.description,
        ug.id AS group_id,
        ug.short_name AS group_name,
        u.id AS user_id,
        u.email
      FROM 
        public.projects_projecttask pt
      JOIN citsci_platform.public.projects_projecttaskgroupvisibility ptgv ON pt.id = ptgv.project_task_id
      JOIN projects_usergroup ug on ptgv.user_group_id = ug.id
      JOIN projects_usergroupmembership ugm on ug.id = ugm.user_group_id
      JOIN projects_user u ON ugm.user_id = u.id  
    """

    return execute_query(base_sql, None, 'dummy-id')


if __name__ == "__main__":
    result = project_task_group_users()
    for r in result:
        print(str(r))
