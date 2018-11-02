DROP TABLE IF EXISTS public.projects_projecttaskgroupvisibility CASCADE;

CREATE TABLE public.projects_projecttaskgroupvisibility
(
    id uuid NOT NULL,
    created timestamp with time zone NOT NULL,
    modified timestamp with time zone NOT NULL,
    project_task_id uuid NOT NULL,
    user_group_id uuid NOT NULL,
    CONSTRAINT projects_projecttaskgroupvisibility_pkey PRIMARY KEY (id),
    CONSTRAINT projects_projecttask_project_task_id_922f5362_fk_projects_ FOREIGN KEY (project_task_id)
        REFERENCES public.projects_projecttask (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT projects_projecttask_user_group_id_040f6e1f_fk_projects_ FOREIGN KEY (user_group_id)
        REFERENCES public.projects_usergroup (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        DEFERRABLE INITIALLY DEFERRED
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

CREATE INDEX projects_projecttaskgroupvisibility_project_task_id_922f5362
    ON public.projects_projecttaskgroupvisibility USING btree
    (project_task_id)
    TABLESPACE pg_default;

CREATE INDEX projects_projecttaskgroupvisibility_user_group_id_040f6e1f
    ON public.projects_projecttaskgroupvisibility USING btree
    (user_group_id)
    TABLESPACE pg_default;