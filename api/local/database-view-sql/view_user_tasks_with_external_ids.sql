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

/*
 Purpose: To list all user tasks together with the internal and external ids, together with useful identifying info, names etc.  Returns one row per user task.
 Usage:  For manual querying.  Not used in code.
 */
CREATE OR REPLACE VIEW public.user_tasks_with_external_ids AS
    SELECT
        u.id AS user_id,
        u.email,
        u.first_name,
        u.last_name,
        ut.id AS user_task_id,
        ut.ext_user_task_id,
        ut.created as usre_task_created,
        up.id AS user_project_id,
        up.ext_user_project_id,
        pt.id AS project_task_id,
        pt.description AS project_task_description,
        p.id AS project_id,
        p.name AS project_name
    FROM projects_user u
    JOIN projects_userproject up on u.id = up.user_id
    JOIN projects_project p on up.project_id = p.id
    JOIN projects_usertask ut on up.id = ut.user_project_id
    JOIN projects_projecttask pt on pt.id = ut.project_task_id;
