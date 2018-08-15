CREATE TABLE public.projects_usertask
(
    id uuid NOT NULL,
    created timestamp with time zone NOT NULL,
    modified timestamp with time zone NOT NULL,
    task_id uuid NOT NULL,
    user_project_id uuid NOT NULL,
    consented timestamp with time zone,
    status character varying(12) COLLATE pg_catalog."default",
    CONSTRAINT projects_usertask_pkey PRIMARY KEY (id),
    CONSTRAINT projects_usertask_task_id_83bf2e62_fk_projects_task_id FOREIGN KEY (task_id)
        REFERENCES public.projects_task (id) MATCH SIMPLE
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

CREATE INDEX projects_usertask_task_id_83bf2e62
    ON public.projects_usertask USING btree
    (task_id)
    TABLESPACE pg_default;

CREATE INDEX projects_usertask_user_project_id_152dcd84
    ON public.projects_usertask USING btree
    (user_project_id)
    TABLESPACE pg_default;