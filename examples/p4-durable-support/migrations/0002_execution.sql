-- Task 2 is a scheduling boundary only. Task 3 adds outbox/delivery tables.
ALTER TABLE tasks
  ADD COLUMN deadline timestamptz NOT NULL DEFAULT (now() + interval '5 minutes'),
  ADD COLUMN lease_owner text,
  ADD COLUMN lease_until timestamptz,
  ADD COLUMN execution_epoch bigint NOT NULL DEFAULT 0 CHECK (execution_epoch >= 0),
  ADD COLUMN checkpoint jsonb NOT NULL DEFAULT '{}',
  ADD COLUMN next_retry_at timestamptz,
  ADD COLUMN cancel_requested boolean NOT NULL DEFAULT false;
CREATE TABLE tenant_policies (
  tenant_id text PRIMARY KEY REFERENCES tenants(tenant_id),
  version bigint NOT NULL DEFAULT 1 CHECK (version > 0)
);
CREATE TABLE resources (
  tenant_id text NOT NULL REFERENCES tenants(tenant_id),
  resource_id text NOT NULL,
  version bigint NOT NULL DEFAULT 1,
  acl_version bigint NOT NULL DEFAULT 1,
  deleted_at timestamptz,
  PRIMARY KEY (tenant_id,resource_id)
);
CREATE TABLE resource_acl (
  tenant_id text NOT NULL,
  resource_id text NOT NULL,
  caller_id text NOT NULL,
  allowed boolean NOT NULL DEFAULT true,
  PRIMARY KEY (tenant_id,resource_id,caller_id),
  FOREIGN KEY (tenant_id,resource_id) REFERENCES resources(tenant_id,resource_id),
  FOREIGN KEY (tenant_id,caller_id) REFERENCES caller_identities(tenant_id,caller_id)
);
ALTER TABLE tasks ADD CONSTRAINT task_tenant_execution UNIQUE(id,tenant_id);
CREATE TABLE actions (
  id uuid PRIMARY KEY,
  task_id uuid NOT NULL REFERENCES tasks(id),
  tenant_id text NOT NULL,
  turn_epoch bigint NOT NULL,
  turn_id uuid NOT NULL,
  position integer NOT NULL,
  tool_call_id text NOT NULL,
  tool text NOT NULL,
  args jsonb NOT NULL,
  canonical_args_hash text NOT NULL,
  resource_id text,
  resource_version bigint,
  acl_version bigint,
  policy_version bigint,
  requires_approval boolean NOT NULL,
  status text NOT NULL CHECK (status IN ('proposed','waiting_approval','authorized_pending_delivery','denied','invalidated','cancelled','succeeded')),
  result jsonb,
  created_at timestamptz NOT NULL DEFAULT now(),
  UNIQUE(task_id,turn_id,position),
  UNIQUE(id,tenant_id),
  UNIQUE(id,task_id,tenant_id),
  FOREIGN KEY (task_id,tenant_id) REFERENCES tasks(id,tenant_id),
  FOREIGN KEY (tenant_id,resource_id) REFERENCES resources(tenant_id,resource_id)
);
CREATE TABLE approvals (
  id uuid PRIMARY KEY,
  task_id uuid NOT NULL REFERENCES tasks(id),
  tenant_id text NOT NULL,
  action_id uuid NOT NULL,
  args_hash text NOT NULL,
  resource_version bigint NOT NULL,
  acl_version bigint NOT NULL,
  policy_version bigint NOT NULL,
  eligible_approver text NOT NULL,
  requested_by text NOT NULL,
  decided_by text,
  expires_at timestamptz NOT NULL,
  status text NOT NULL DEFAULT 'pending' CHECK (status IN ('pending','approved','denied','cancelled')),
  decided_at timestamptz,
  UNIQUE(action_id),
  FOREIGN KEY (action_id,task_id,tenant_id) REFERENCES actions(id,task_id,tenant_id),
  FOREIGN KEY (tenant_id,eligible_approver) REFERENCES caller_identities(tenant_id,caller_id),
  FOREIGN KEY (tenant_id,requested_by) REFERENCES caller_identities(tenant_id,caller_id),
  FOREIGN KEY (tenant_id,decided_by) REFERENCES caller_identities(tenant_id,caller_id)
);
CREATE TABLE index_versions (
  id uuid PRIMARY KEY,
  tenant_id text NOT NULL REFERENCES tenants(tenant_id),
  state text NOT NULL DEFAULT 'building' CHECK (state IN ('building','validated','active','retired')),
  UNIQUE(id,tenant_id)
);
CREATE UNIQUE INDEX one_active_index ON index_versions(tenant_id) WHERE state='active';
CREATE TABLE documents (
  id uuid PRIMARY KEY,
  tenant_id text NOT NULL,
  resource_id text NOT NULL,
  doc_version bigint NOT NULL,
  content_hash text NOT NULL,
  acl_version bigint NOT NULL,
  index_version uuid NOT NULL,
  deleted_at timestamptz,
  UNIQUE (id,tenant_id,resource_id),
  UNIQUE (tenant_id,resource_id,index_version),
  FOREIGN KEY (tenant_id,resource_id) REFERENCES resources(tenant_id,resource_id),
  FOREIGN KEY (index_version,tenant_id) REFERENCES index_versions(id,tenant_id)
);
CREATE TABLE chunks (
  id uuid PRIMARY KEY,
  document_id uuid NOT NULL,
  tenant_id text NOT NULL,
  resource_id text NOT NULL,
  position integer NOT NULL,
  body text NOT NULL,
  FOREIGN KEY (document_id,tenant_id,resource_id) REFERENCES documents(id,tenant_id,resource_id),
  UNIQUE (document_id,position)
);
-- Cache and memory are provenance records, never an authorization shortcut.
CREATE TABLE context_cache (
  tenant_id text NOT NULL,
  caller_id text NOT NULL,
  resource_id text NOT NULL,
  chunk_id uuid NOT NULL REFERENCES chunks(id),
  PRIMARY KEY (tenant_id,caller_id,chunk_id),
  FOREIGN KEY (tenant_id,resource_id) REFERENCES resources(tenant_id,resource_id)
);
CREATE TABLE context_memory (LIKE context_cache INCLUDING ALL);
CREATE TABLE service_limits (
  singleton boolean PRIMARY KEY DEFAULT true CHECK (singleton),
  queue_limit integer NOT NULL DEFAULT 10000 CHECK (queue_limit>=0),
  task_limit integer NOT NULL DEFAULT 100 CHECK (task_limit>0)
);
INSERT INTO service_limits(singleton) VALUES (true);
CREATE TABLE task_slots (
  task_id uuid PRIMARY KEY REFERENCES tasks(id),
  owner text NOT NULL,
  epoch bigint NOT NULL,
  expires_at timestamptz NOT NULL
);
CREATE TABLE provider_endpoints (
  id text PRIMARY KEY,
  concurrency_limit integer NOT NULL CHECK (concurrency_limit>0),
  max_attempts integer NOT NULL DEFAULT 3 CHECK (max_attempts>0)
);
CREATE TABLE provider_slots (
  id uuid PRIMARY KEY,
  endpoint text NOT NULL REFERENCES provider_endpoints(id),
  task_id uuid NOT NULL REFERENCES tasks(id),
  owner text NOT NULL,
  epoch bigint NOT NULL,
  expires_at timestamptz NOT NULL
);
CREATE TABLE provider_attempts (
  task_id uuid NOT NULL REFERENCES tasks(id),
  endpoint text NOT NULL REFERENCES provider_endpoints(id),
  attempts integer NOT NULL CHECK (attempts>=0),
  PRIMARY KEY (task_id,endpoint)
);
CREATE TABLE budget_accounts (
  id text PRIMARY KEY,
  tenant_id text NOT NULL REFERENCES tenants(tenant_id),
  token_limit bigint NOT NULL CHECK (token_limit>=0),
  tool_limit bigint NOT NULL CHECK (tool_limit>=0),
  consumed_tokens bigint NOT NULL DEFAULT 0 CHECK (consumed_tokens>=0),
  consumed_tools bigint NOT NULL DEFAULT 0 CHECK (consumed_tools>=0),
  reserved_tokens bigint NOT NULL DEFAULT 0 CHECK (reserved_tokens>=0),
  reserved_tools bigint NOT NULL DEFAULT 0 CHECK (reserved_tools>=0)
);
CREATE TABLE budget_reservations (
  id uuid PRIMARY KEY,
  account text NOT NULL REFERENCES budget_accounts(id),
  task_id uuid NOT NULL REFERENCES tasks(id),
  owner text NOT NULL,
  epoch bigint NOT NULL,
  tokens bigint NOT NULL CHECK (tokens>=0),
  tools bigint NOT NULL CHECK (tools>=0),
  sent boolean NOT NULL DEFAULT false,
  state text NOT NULL DEFAULT 'reserved' CHECK (state IN ('reserved','unknown','settled','released')),
  actual_tokens bigint,
  actual_tools bigint
);
CREATE INDEX execution_queue ON tasks(status,next_retry_at,created_at);
