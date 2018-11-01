DROP TABLE IF EXISTS public.projects_user CASCADE;

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
    email_address_verified boolean NOT NULL,
    email_verification_expiry timestamp with time zone,
    email_verification_token uuid,
    CONSTRAINT projects_user_pkey PRIMARY KEY (id)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;
