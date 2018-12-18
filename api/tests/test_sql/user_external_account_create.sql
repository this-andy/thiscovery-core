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