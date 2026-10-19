CREATE TABLE tenants (
    tenant_id text PRIMARY KEY,
    display_name text NOT NULL
);
CREATE TABLE caller_identities (
    tenant_id text NOT NULL REFERENCES tenants(tenant_id),
    caller_id text NOT NULL,
    active boolean NOT NULL DEFAULT true,
    roles text[] NOT NULL DEFAULT ARRAY['caller'],
    PRIMARY KEY (tenant_id, caller_id)
);
CREATE TABLE tasks (
    id uuid PRIMARY KEY,
    tenant_id text NOT NULL,
    owner_id text NOT NULL,
    status text NOT NULL DEFAULT 'queued' CHECK (status IN
      ('queued', 'running', 'waiting_approval', 'reconciling', 'completed', 'failed', 'cancelled')),
    state_version bigint NOT NULL DEFAULT 1 CHECK (state_version > 0),
    release_id text NOT NULL,
    input jsonb NOT NULL,
    input_hash text NOT NULL,
    last_event_seq bigint NOT NULL DEFAULT 0 CHECK (last_event_seq >= 0),
    created_at timestamptz NOT NULL DEFAULT now(),
    FOREIGN KEY (tenant_id, owner_id) REFERENCES caller_identities(tenant_id, caller_id),
    UNIQUE (id, tenant_id, owner_id)
);
CREATE TABLE events (
    task_id uuid NOT NULL REFERENCES tasks(id),
    seq bigint NOT NULL CHECK (seq > 0),
    kind text NOT NULL,
    payload jsonb NOT NULL,
    redaction_version text NOT NULL DEFAULT 'synthetic-v1',
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (task_id, seq)
);
CREATE FUNCTION reject_event_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
    RAISE EXCEPTION 'events are append-only';
END;
$$;
CREATE TRIGGER immutable_events BEFORE UPDATE OR DELETE OR TRUNCATE ON events
FOR EACH STATEMENT EXECUTE FUNCTION reject_event_mutation();
CREATE TABLE idempotency_records (
    tenant_id text NOT NULL,
    caller_id text NOT NULL,
    idempotency_key text NOT NULL CHECK (length(idempotency_key) BETWEEN 1 AND 200),
    payload_hash text NOT NULL,
    task_id uuid NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now(),
    PRIMARY KEY (tenant_id, caller_id, idempotency_key),
    FOREIGN KEY (tenant_id, caller_id) REFERENCES caller_identities(tenant_id, caller_id),
    FOREIGN KEY (task_id, tenant_id, caller_id) REFERENCES tasks(id, tenant_id, owner_id)
);
CREATE INDEX task_owner_read ON tasks (tenant_id, owner_id, id);
