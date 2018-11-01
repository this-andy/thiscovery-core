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