BEGIN;


ALTER TABLE "user" ADD CONSTRAINT user_pkey PRIMARY KEY (id);
ALTER TABLE dataset ADD CONSTRAINT dataset_pkey PRIMARY KEY (id);
ALTER TABLE dataset_class ADD CONSTRAINT dataset_class_pkey PRIMARY KEY (id);
ALTER TABLE dataset_class_member ADD CONSTRAINT dataset_class_member_pkey PRIMARY KEY (class, mbid);

COMMIT;
