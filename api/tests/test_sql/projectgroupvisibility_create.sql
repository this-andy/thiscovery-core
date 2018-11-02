
DROP TABLE IF EXISTS public.projects_projectgroupvisibility CASCADE;

CREATE TABLE public.projects_projectgroupvisibility
(
    id uuid NOT NULL,
    created timestamp with time zone NOT NULL,
    modified timestamp with time zone NOT NULL,
    project_id uuid NOT NULL,
    user_group_id uuid NOT NULL,
    CONSTRAINT projects_projectgroupvisibility_pkey PRIMARY KEY (id),
    CONSTRAINT projects_projectgrou_project_id_05ae8023_fk_projects_ FOREIGN KEY (project_id)
        REFERENCES public.projects_project (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT projects_projectgrou_user_group_id_50bae39b_fk_projects_ FOREIGN KEY (user_group_id)
        REFERENCES public.projects_usergroup (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        DEFERRABLE INITIALLY DEFERRED
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

CREATE INDEX projects_projectgroupvisibility_project_id_05ae8023
    ON public.projects_projectgroupvisibility USING btree
    (project_id)
    TABLESPACE pg_default;

CREATE INDEX projects_projectgroupvisibility_user_group_id_50bae39b
    ON public.projects_projectgroupvisibility USING btree
    (user_group_id)
    TABLESPACE pg_default;