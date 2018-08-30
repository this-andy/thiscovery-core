CREATE TABLE public.projects_entityupdate
(
    id uuid NOT NULL,
    created timestamp with time zone NOT NULL,
    modified timestamp with time zone NOT NULL,
    entity_name character varying(50) COLLATE pg_catalog."default" NOT NULL,
    entity_id uuid NOT NULL,
    json_patch character varying(2000) COLLATE pg_catalog."default" NOT NULL,
    json_reverse_patch character varying(2000) COLLATE pg_catalog."default" NOT NULL,
    CONSTRAINT projects_entityupdate_pkey PRIMARY KEY (id)
)
WITH (
    OIDS = FALSE
)
TABLESPACE pg_default;
