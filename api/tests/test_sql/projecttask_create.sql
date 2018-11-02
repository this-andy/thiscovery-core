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
    CONSTRAINT projects_projecttask_pkey PRIMARY KEY (id),
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