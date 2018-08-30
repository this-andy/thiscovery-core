CREATE TABLE public.projects_user
(
    id uuid NOT NULL,
    created timestamp with time zone NOT NULL,
    modified timestamp with time zone NOT NULL,
    email character varying(100) COLLATE pg_catalog."default",
    title character varying(20) COLLATE pg_catalog."default",
    first_name character varying(50) COLLATE pg_catalog."default",
    last_name character varying(50) COLLATE pg_catalog."default",
    auth0_id character varying(50) COLLATE pg_catalog."default",
    status character varying(12) COLLATE pg_catalog."default",
    CONSTRAINT projects_user_pkey PRIMARY KEY (id)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;
