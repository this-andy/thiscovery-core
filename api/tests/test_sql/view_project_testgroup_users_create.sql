CREATE OR REPLACE VIEW public.project_testgroup_users AS
 SELECT p.id AS project_id,
    p.short_name AS project_name,
    p.testing_group_id,
    ug.short_name AS group_name,
    u.id AS user_id,
    u.email
   FROM projects_project p
     JOIN projects_usergroup ug ON ug.id = p.testing_group_id
     JOIN projects_usergroupmembership ugm ON ug.id = ugm.user_group_id
     JOIN projects_user u ON ugm.user_id = u.id;
