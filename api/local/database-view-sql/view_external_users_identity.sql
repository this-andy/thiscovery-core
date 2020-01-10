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

CREATE OR REPLACE VIEW public.external_users_identity AS
    SELECT
        u.id AS user_id,
        u.email,
        u.first_name,
        u.last_name,
        ut.id AS user_task_id,
        ut.ext_user_task_id,
        up.id AS user_project_id,
        up.ext_user_project_id,
        pt.id AS project_task_id,
        p.id AS project_id
    FROM projects_user u
    JOIN projects_userproject up on u.id = up.user_id
    JOIN projects_project p on up.project_id = p.id
    JOIN projects_usertask ut on up.id = ut.user_project_id
    JOIN projects_projecttask pt on pt.project_id = p.id;
