CREATE OR REPLACE VIEW public.project_group_users AS
 SELECT p.id AS project_id,
    p.short_name AS project_name,
    ug.id AS group_id,
    ug.short_name AS group_name,
    u.id AS user_id,
    u.email
   FROM projects_project p
     JOIN projects_projectgroupvisibility pgv ON p.id = pgv.project_id
     JOIN projects_usergroup ug ON pgv.user_group_id = ug.id
     JOIN projects_usergroupmembership ugm ON ug.id = ugm.user_group_id
     JOIN projects_user u ON ugm.user_id = u.id;



