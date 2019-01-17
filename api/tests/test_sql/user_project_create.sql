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

DROP TABLE IF EXISTS public.projects_userproject CASCADE;

CREATE TABLE public.projects_userproject
(
    id uuid NOT NULL,
    created timestamp with time zone NOT NULL,
    modified timestamp with time zone NOT NULL,
    project_id uuid NOT NULL,
    status character varying(12) COLLATE pg_catalog."default",
    user_id uuid NOT NULL,
    CONSTRAINT projects_userproject_pkey PRIMARY KEY (id),
    CONSTRAINT projects_userproject_project_id_5148b8ce_fk_projects_project_id FOREIGN KEY (project_id)
        REFERENCES public.projects_project (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT projects_userproject_user_id_2d5013b8_fk_projects_user_id FOREIGN KEY (user_id)
        REFERENCES public.projects_user (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        DEFERRABLE INITIALLY DEFERRED
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;


CREATE INDEX projects_userproject_project_id_5148b8ce
    ON public.projects_userproject USING btree
    (project_id)
    TABLESPACE pg_default;

CREATE INDEX projects_userproject_user_id_2d5013b8
    ON public.projects_userproject USING btree
    (user_id)
    TABLESPACE pg_default;