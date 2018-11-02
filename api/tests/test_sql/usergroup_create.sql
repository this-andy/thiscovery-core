DROP TABLE IF EXISTS public.projects_usergroup CASCADE;

CREATE TABLE public.projects_usergroup
(
    id uuid NOT NULL,
    created timestamp with time zone NOT NULL,
    modified timestamp with time zone NOT NULL,
    name character varying(50) COLLATE pg_catalog."default" NOT NULL,
    short_name character varying(20) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT projects_usergroup_pkey PRIMARY KEY (id)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;
