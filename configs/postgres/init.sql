CREATE TABLE IF NOT EXISTS "tenant" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(255) NOT NULL UNIQUE
);

CREATE TABLE IF NOT EXISTS "user" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "username" VARCHAR(128) NOT NULL UNIQUE,
    "hashed_password" VARCHAR(512) NOT NULL,
    "tenant_id" INT NOT NULL REFERENCES "tenant" ("id") ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "scanner" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "name" VARCHAR(128) NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL,
    "tenant_id" INT NOT NULL REFERENCES "tenant" ("id") ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "scanjob" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "ip_network" VARCHAR(128) NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL,
    "finished_at" TIMESTAMPTZ,
    "status" VARCHAR(32) NOT NULL,
    "scanner_id" INT NOT NULL REFERENCES "scanner" ("id") ON DELETE CASCADE,
    "tenant_id" INT NOT NULL REFERENCES "tenant" ("id") ON DELETE CASCADE
);

COMMENT ON COLUMN "scanjob"."status" IS 'PENDING: pending
RUNNING: running
FINISHED: finished
FAILED: failed';

CREATE TABLE IF NOT EXISTS "host" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "ip" INET NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "tenant_id" INT NOT NULL REFERENCES "tenant" ("id") ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "port" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "number" INT NOT NULL,
    "service_name" VARCHAR(128) NOT NULL,
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "tenant_id" INT NOT NULL REFERENCES "tenant" ("id") ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "hostport" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "created_at" TIMESTAMPTZ NOT NULL,
    "updated_at" TIMESTAMPTZ NOT NULL,
    "host_id" INT NOT NULL REFERENCES "host" ("id") ON DELETE CASCADE,
    "port_id" INT NOT NULL REFERENCES "port" ("id") ON DELETE CASCADE,
    "tenant_id" INT NOT NULL REFERENCES "tenant" ("id") ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "scanjobhostdiscovery" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "host_id" INT NOT NULL REFERENCES "host" ("id") ON DELETE CASCADE,
    "scan_job_id" INT NOT NULL REFERENCES "scanjob" ("id") ON DELETE CASCADE,
    "tenant_id" INT NOT NULL REFERENCES "tenant" ("id") ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS "scanjobportdiscovery" (
    "id" SERIAL NOT NULL PRIMARY KEY,
    "host_port_id" INT NOT NULL REFERENCES "hostport" ("id") ON DELETE CASCADE,
    "scan_job_id" INT NOT NULL REFERENCES "scanjob" ("id") ON DELETE CASCADE,
    "tenant_id" INT NOT NULL REFERENCES "tenant" ("id") ON DELETE CASCADE
);
