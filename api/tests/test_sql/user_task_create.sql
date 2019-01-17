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

DROP TABLE IF EXISTS public.projects_usertask CASCADE;

CREATE TABLE public.projects_usertask
(
    id uuid NOT NULL,
    created timestamp with time zone NOT NULL,
    modified timestamp with time zone NOT NULL,
    user_project_id uuid NOT NULL,
    consented timestamp with time zone,
    status character varying(12) COLLATE pg_catalog."default",
    project_task_id uuid NOT NULL,
    CONSTRAINT projects_usertask_pkey PRIMARY KEY (id),
    CONSTRAINT projects_usertask_project_task_id_9b4cf6f5_fk_projects_ FOREIGN KEY (project_task_id)
        REFERENCES public.projects_projecttask (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT projects_usertask_user_project_id_152dcd84_fk_projects_ FOREIGN KEY (user_project_id)
        REFERENCES public.projects_userproject (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        DEFERRABLE INITIALLY DEFERRED
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

CREATE INDEX projects_usertask_project_task_id_9b4cf6f5
    ON public.projects_usertask USING btree
    (project_task_id)
    TABLESPACE pg_default;

CREATE INDEX projects_usertask_user_project_id_152dcd84
    ON public.projects_usertask USING btree
    (user_project_id)
    TABLESPACE pg_default;