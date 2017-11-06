BEGIN;

CREATE TABLE "user" (
  id             SERIAL,
  created        TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  musicbrainz_id VARCHAR,
  admin          BOOLEAN NOT NULL         DEFAULT FALSE
);
ALTER TABLE "user" ADD CONSTRAINT user_musicbrainz_id_key UNIQUE (musicbrainz_id);

CREATE TABLE dataset (
  id          UUID,
  name        VARCHAR NOT NULL,
  description TEXT,
  author      INT NOT NULL, -- FK to user
  public      BOOLEAN NOT NULL,
  created     TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  last_edited TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE TABLE dataset_class (
  id          SERIAL,
  name        VARCHAR NOT NULL,
  description TEXT,
  dataset     UUID    NOT NULL -- FK to dataset
);

CREATE TABLE dataset_class_member (
  class INT, -- FK to class
  mbid  UUID
);

CREATE TABLE api_key (
  value     TEXT    NOT NULL,
  is_active BOOLEAN NOT NULL         DEFAULT TRUE,
  owner     INTEGER NOT NULL,
  created   TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

COMMIT;
