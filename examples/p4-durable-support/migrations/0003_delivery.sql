-- Extend states without changing checksummed execution migration 0002.
ALTER TABLE actions DROP CONSTRAINT actions_status_check;
ALTER TABLE actions ADD CONSTRAINT actions_status_check CHECK (status IN
 ('proposed','waiting_approval','authorized_pending_delivery','authorized','dispatching',
  'unknown','denied','invalidated','cancelled','succeeded'));
CREATE TABLE outbox (
 action_id uuid PRIMARY KEY,
 task_id uuid NOT NULL,
 tenant_id text NOT NULL,
 external_key text NOT NULL UNIQUE,
 payload jsonb NOT NULL,
 status text NOT NULL DEFAULT 'queued' CHECK (status IN
  ('queued','dispatching','unknown','succeeded','invalidated','cancelled')),
 scheduled_epoch bigint NOT NULL CHECK (scheduled_epoch>0),
 dispatch_token uuid,
 claim_until timestamptz,
 attempts integer NOT NULL DEFAULT 0 CHECK (attempts>=0),
 receipt jsonb,
 created_at timestamptz NOT NULL DEFAULT now(),
 FOREIGN KEY (action_id,task_id,tenant_id) REFERENCES actions(id,task_id,tenant_id),
 CHECK (external_key='p4-notice:'||action_id::text),
 CHECK ((status='succeeded')=(receipt IS NOT NULL)),
 CHECK (status NOT IN ('dispatching','unknown') OR (dispatch_token IS NOT NULL AND claim_until IS NOT NULL))
);
CREATE INDEX delivery_recovery ON outbox(status,claim_until);
-- The sink is a separate HTTP process. Its synthetic effect and durable receipt
-- commit in one receiver transaction, independent of task/outbox transactions.
CREATE TABLE sink_receipts (
 external_key text PRIMARY KEY,
 action_id uuid NOT NULL,
 tenant_id text NOT NULL,
 payload_hash text NOT NULL,
 receipt jsonb NOT NULL,
 created_at timestamptz NOT NULL DEFAULT now(),
 CHECK (external_key='p4-notice:'||action_id::text)
);
CREATE TABLE sink_effects (
 receipt_id uuid PRIMARY KEY,
 external_key text NOT NULL UNIQUE REFERENCES sink_receipts(external_key),
 action_id uuid NOT NULL,
 tenant_id text NOT NULL,
 resource_id text NOT NULL,
 message text NOT NULL
);
CREATE TABLE sink_requests (
 seq bigint GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
 external_key text NOT NULL,
 method text NOT NULL CHECK (method IN ('GET','POST')),
 created_at timestamptz NOT NULL DEFAULT now()
);
