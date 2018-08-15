CREATE TABLE public.users_user
(
    id integer NOT NULL,
    password character varying(128) COLLATE pg_catalog."default" NOT NULL,
    last_login timestamp with time zone,
    is_superuser boolean NOT NULL,
    username character varying(150) COLLATE pg_catalog."default" NOT NULL,
    first_name character varying(30) COLLATE pg_catalog."default" NOT NULL,
    last_name character varying(30) COLLATE pg_catalog."default" NOT NULL,
    email character varying(254) COLLATE pg_catalog."default" NOT NULL,
    is_staff boolean NOT NULL,
    is_active boolean NOT NULL,
    date_joined timestamp with time zone NOT NULL,
    name character varying(255) COLLATE pg_catalog."default" NOT NULL,
    uuid uuid NOT NULL,
    CONSTRAINT users_user_pkey PRIMARY KEY (id),
    CONSTRAINT users_user_username_key UNIQUE (username),
    CONSTRAINT users_user_uuid_key UNIQUE (uuid)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;

CREATE INDEX users_user_username_06e46fe6_like
    ON public.users_user USING btree
    (username COLLATE pg_catalog."default" varchar_pattern_ops)
    TABLESPACE pg_default;