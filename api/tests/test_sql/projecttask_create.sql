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

DROP TABLE IF EXISTS public.projects_projecttask CASCADE;

CREATE TABLE public.projects_projecttask
(
    id uuid NOT NULL,
    created timestamp with time zone NOT NULL,
    modified timestamp with time zone NOT NULL,
    description character varying(500) COLLATE pg_catalog."default" NOT NULL,
    status character varying(12) COLLATE pg_catalog."default" NOT NULL,
    project_id uuid NOT NULL,
    task_type_id uuid NOT NULL,
    closing_date timestamp with time zone,
    earliest_start_date timestamp with time zone,
    signup_status character varying(12) COLLATE pg_catalog."default" NOT NULL,
    website_highlight boolean NOT NULL,
    visibility character varying(12) COLLATE pg_catalog."default" NOT NULL,
    testing_group_id uuid,
    external_task_id character varying(50) COLLATE pg_catalog."default",
    external_system_id uuid,
    base_url character varying(100) COLLATE pg_catalog."default",
    CONSTRAINT projects_projecttask_pkey PRIMARY KEY (id),
    CONSTRAINT projects_projecttask_external_system_id_0d9467a7_fk_projects_ FOREIGN KEY (external_system_id)
        REFERENCES public.projects_externalsystem (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT projects_projecttask_project_id_c579add0_fk_projects_project_id FOREIGN KEY (project_id)
        REFERENCES public.projects_project (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT projects_projecttask_task_type_id_fce5c6e0_fk_projects_ FOREIGN KEY (task_type_id)
        REFERENCES public.projects_tasktype (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT projects_projecttask_testing_group_id_b3d82910_fk_projects_ FOREIGN KEY (testing_group_id)
        REFERENCES public.projects_usergroup (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        DEFERRABLE INITIALLY DEFERRED
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

CREATE INDEX projects_projecttask_project_id_c579add0
    ON public.projects_projecttask USING btree
    (project_id)
    TABLESPACE pg_default;

CREATE INDEX projects_projecttask_task_type_id_fce5c6e0
    ON public.projects_projecttask USING btree
    (task_type_id)
    TABLESPACE pg_default;

CREATE INDEX projects_projecttask_testing_group_id_b3d82910
    ON public.projects_projecttask USING btree
    (testing_group_id)
    TABLESPACE pg_default;