-- Preserve the checksummed 0003 schema for already initialized databases.
ALTER TABLE actions DROP CONSTRAINT actions_status_check;
ALTER TABLE actions ADD CONSTRAINT actions_status_check CHECK (status IN
 ('proposed','waiting_approval','authorized_pending_delivery','authorized','dispatching',
  'unknown','denied','invalidated','failed','cancelled','succeeded'));
ALTER TABLE outbox DROP CONSTRAINT outbox_status_check;
ALTER TABLE outbox ADD CONSTRAINT outbox_status_check CHECK (status IN
 ('queued','dispatching','unknown','succeeded','invalidated','failed','cancelled'));
CREATE TABLE manual_delivery_resolutions (
 id uuid PRIMARY KEY,
 action_id uuid NOT NULL UNIQUE,
 task_id uuid NOT NULL,
 tenant_id text NOT NULL,
 operator_id text NOT NULL,
 dispatch_token uuid NOT NULL,
 external_key text NOT NULL,
 outcome text NOT NULL CHECK (outcome IN ('effect_applied','effect_not_applied','abandon')),
 evidence_reference text NOT NULL CHECK (length(btrim(evidence_reference)) BETWEEN 1 AND 1024),
 reason text NOT NULL CHECK (length(btrim(reason)) BETWEEN 1 AND 2000),
 created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
 FOREIGN KEY (action_id,task_id,tenant_id) REFERENCES actions(id,task_id,tenant_id),
 FOREIGN KEY (tenant_id,operator_id) REFERENCES caller_identities(tenant_id,caller_id),
 CHECK (external_key='p4-notice:'||action_id::text)
);
CREATE TRIGGER immutable_manual_delivery_resolutions
 BEFORE UPDATE OR DELETE OR TRUNCATE ON manual_delivery_resolutions
 FOR EACH STATEMENT EXECUTE FUNCTION reject_event_mutation();
