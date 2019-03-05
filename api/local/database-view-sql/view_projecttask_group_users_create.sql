/*
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
#   You should have received a copy of the GNU Affero General Public License
#   along with this program.  If not, see <https://www.gnu.org/licenses/>.
*/

CREATE OR REPLACE VIEW public.projecttask_group_users AS
 SELECT pt.id AS project_task_id,
    pt.description,
    ug.id AS group_id,
    ug.short_name AS group_name,
    u.id AS user_id,
    u.email
   FROM projects_projecttask pt
     JOIN projects_projecttaskgroupvisibility ptgv ON pt.id = ptgv.project_task_id
     JOIN projects_usergroup ug ON ptgv.user_group_id = ug.id
     JOIN projects_usergroupmembership ugm ON ug.id = ugm.user_group_id
     JOIN projects_user u ON ugm.user_id = u.id;
