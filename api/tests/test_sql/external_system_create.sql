DROP TABLE IF EXISTS public.projects_externalsystem CASCADE;

CREATE TABLE public.projects_externalsystem
(
    id uuid NOT NULL,
    created timestamp with time zone NOT NULL,
    modified timestamp with time zone NOT NULL,
    name character varying(50) COLLATE pg_catalog."default" NOT NULL,
    short_name character varying(20) COLLATE pg_catalog."default" NOT NULL,
    external_user_id_type character varying(10) COLLATE pg_catalog."default",
    CONSTRAINT projects_externalsystem_pkey PRIMARY KEY (id)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;
