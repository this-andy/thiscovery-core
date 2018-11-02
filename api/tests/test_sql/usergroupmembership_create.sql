DROP TABLE IF EXISTS public.projects_usergroupmembership CASCADE;

CREATE TABLE public.projects_usergroupmembership
(
    id uuid NOT NULL,
    created timestamp with time zone NOT NULL,
    modified timestamp with time zone NOT NULL,
    user_id uuid NOT NULL,
    user_group_id uuid NOT NULL,
    CONSTRAINT projects_usergroupmembership_pkey PRIMARY KEY (id),
    CONSTRAINT projects_usergroupme_user_group_id_019b4dd4_fk_projects_ FOREIGN KEY (user_group_id)
        REFERENCES public.projects_usergroup (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        DEFERRABLE INITIALLY DEFERRED,
    CONSTRAINT projects_usergroupme_user_id_4ed3afd8_fk_projects_ FOREIGN KEY (user_id)
        REFERENCES public.projects_user (id) MATCH SIMPLE
        ON UPDATE NO ACTION
        ON DELETE NO ACTION
        DEFERRABLE INITIALLY DEFERRED
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

CREATE INDEX projects_usergroupmembership_user_group_id_019b4dd4
    ON public.projects_usergroupmembership USING btree
    (user_group_id)
    TABLESPACE pg_default;

CREATE INDEX projects_usergroupmembership_user_id_4ed3afd8
    ON public.projects_usergroupmembership USING btree
    (user_id)
    TABLESPACE pg_default;