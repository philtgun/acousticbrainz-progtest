BEGIN;

ALTER TABLE dataset
  ADD CONSTRAINT dataset_fk_user
  FOREIGN KEY (author)
  REFERENCES "user" (id)
  ON UPDATE CASCADE
  ON DELETE CASCADE;

ALTER TABLE dataset_class
  ADD CONSTRAINT class_fk_dataset
  FOREIGN KEY (dataset)
  REFERENCES dataset (id)
  ON UPDATE CASCADE
  ON DELETE CASCADE;

ALTER TABLE dataset_class_member
  ADD CONSTRAINT class_member_fk_class
  FOREIGN KEY (class)
  REFERENCES dataset_class (id)
  ON UPDATE CASCADE
  ON DELETE CASCADE;

ALTER TABLE api_key
  ADD CONSTRAINT api_key_fk_user
  FOREIGN KEY (owner)
  REFERENCES "user" (id);

COMMIT;
