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

DROP TABLE IF EXISTS public.projects_projectgroupvisibility CASCADE;

CREATE TABLE public.projects_projectgroupvisibility
(
    id uuid NOT NULL,
    created timestamp with time zone NOT NULL,
    modified timestamp with time zone NOT NULL,
    project_id uuid NOT NULL,
    user_group_id uuid NOT NULL,
    CONSTRAINT projects_projectgroupvisibility_pkey PRIMARY KEY (id),
    CONSTRAINT projects_projectgrou_project_id_05ae8023_fk_projects_ FOREIGN KEY (project_id)
        REFERENCES public.projects_project (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT projects_projectgrou_user_group_id_50bae39b_fk_projects_ FOREIGN KEY (user_group_id)
        REFERENCES public.projects_usergroup (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        DEFERRABLE INITIALLY DEFERRED
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

CREATE INDEX projects_projectgroupvisibility_project_id_05ae8023
    ON public.projects_projectgroupvisibility USING btree
    (project_id)
    TABLESPACE pg_default;

CREATE INDEX projects_projectgroupvisibility_user_group_id_50bae39b
    ON public.projects_projectgroupvisibility USING btree
    (user_group_id)
    TABLESPACE pg_default;