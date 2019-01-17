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

DROP TABLE IF EXISTS public.projects_userexternalaccount CASCADE;

CREATE TABLE public.projects_userexternalaccount
(
    id uuid NOT NULL,
    created timestamp with time zone NOT NULL,
    modified timestamp with time zone NOT NULL,
    external_user_id character varying(50) COLLATE pg_catalog."default",
    status character varying(12) COLLATE pg_catalog."default",
    external_system_id uuid NOT NULL,
    user_id uuid NOT NULL,
    CONSTRAINT projects_userexternalaccount_pkey PRIMARY KEY (id),
    CONSTRAINT projects_userexterna_external_system_id_caa20537_fk_projects_ FOREIGN KEY (external_system_id)
        REFERENCES public.projects_externalsystem (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT projects_userexterna_user_id_f56ae6d3_fk_projects_ FOREIGN KEY (user_id)
        REFERENCES public.projects_user (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        DEFERRABLE INITIALLY DEFERRED
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

CREATE INDEX projects_userexternalaccount_external_system_id_caa20537
    ON public.projects_userexternalaccount USING btree
    (external_system_id)
    TABLESPACE pg_default;

CREATE INDEX projects_userexternalaccount_user_id_f56ae6d3
    ON public.projects_userexternalaccount USING btree
    (user_id)
    TABLESPACE pg_default;