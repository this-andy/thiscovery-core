DROP TABLE IF EXISTS public.projects_project CASCADE;

CREATE TABLE public.projects_project
(
    id uuid NOT NULL,
    created timestamp with time zone NOT NULL,
    modified timestamp with time zone NOT NULL,
    name character varying(50) COLLATE pg_catalog."default" NOT NULL,
    short_name character varying(20) COLLATE pg_catalog."default" NOT NULL,
    status character varying(12) COLLATE pg_catalog."default" NOT NULL,
    website_highlight boolean NOT NULL,
    visibility character varying(12) COLLATE pg_catalog."default" NOT NULL,
    testing_group_id uuid,
    CONSTRAINT projects_project_pkey PRIMARY KEY (id),
    CONSTRAINT projects_project_testing_group_id_bb4dd85f_fk_projects_ FOREIGN KEY (testing_group_id)
        REFERENCES public.projects_usergroup (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        DEFERRABLE INITIALLY DEFERRED
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

CREATE INDEX projects_project_testing_group_id_bb4dd85f
    ON public.projects_project USING btree
    (testing_group_id)
    TABLESPACE pg_default;