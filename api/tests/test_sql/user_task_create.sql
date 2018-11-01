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