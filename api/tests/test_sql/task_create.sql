CREATE TABLE public.projects_task
(
    id uuid NOT NULL,
    created timestamp with time zone NOT NULL,
    modified timestamp with time zone NOT NULL,
    description character varying(500) COLLATE pg_catalog."default" NOT NULL,
    project_id uuid NOT NULL,
    task_type_id uuid NOT NULL,
    status character varying(12) COLLATE pg_catalog."default",
    CONSTRAINT projects_task_pkey PRIMARY KEY (id),
    CONSTRAINT projects_task_project_id_a1b987d6_fk_projects_project_id FOREIGN KEY (project_id)
        REFERENCES public.projects_project (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT projects_task_task_type_id_dac99a35_fk_projects_tasktype_id FOREIGN KEY (task_type_id)
        REFERENCES public.projects_tasktype (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        DEFERRABLE INITIALLY DEFERRED
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

CREATE INDEX projects_task_project_id_a1b987d6
    ON public.projects_task USING btree
    (project_id)
    TABLESPACE pg_default;

CREATE INDEX projects_task_task_type_id_dac99a35
    ON public.projects_task USING btree
    (task_type_id)
    TABLESPACE pg_default;