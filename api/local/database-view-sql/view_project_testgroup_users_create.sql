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

CREATE OR REPLACE VIEW public.project_testgroup_users AS
 SELECT p.id AS project_id,
    p.short_name AS project_name,
    p.testing_group_id,
    ug.short_name AS group_name,
    u.id AS user_id,
    u.email,
    up.ext_user_project_id AS ext_user_project_id
   FROM projects_project p
     JOIN projects_usergroup ug ON ug.id = p.testing_group_id
     JOIN projects_usergroupmembership ugm ON ug.id = ugm.user_group_id
     JOIN projects_user u ON ugm.user_id = u.id
     JOIN projects_userproject up ON p.id = up.project_id;
