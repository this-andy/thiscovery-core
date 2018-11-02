CREATE OR REPLACE VIEW public.projecttask_testgroup_users AS
 SELECT pt.id AS project_task_id,
    pt.description,
    pt.testing_group_id,
    ug.short_name AS group_name,
    u.id AS user_id,
    u.email
   FROM projects_projecttask pt
     JOIN projects_usergroup ug ON ug.id = pt.testing_group_id
     JOIN projects_usergroupmembership ugm ON ug.id = ugm.user_group_id
     JOIN projects_user u ON ugm.user_id = u.id;
