-- Provider calls have a durable send boundary. A sending row is ambiguous after
-- owner loss and must never be recreated as a retry of the same request.
CREATE TABLE provider_calls (
  request_id uuid PRIMARY KEY,
  task_id uuid NOT NULL REFERENCES tasks(id),
  round_index integer NOT NULL CHECK (round_index >= 0),
  endpoint text NOT NULL REFERENCES provider_endpoints(id),
  release_id text NOT NULL,
  model text NOT NULL CHECK (length(btrim(model)) BETWEEN 1 AND 200),
  owner text NOT NULL,
  epoch bigint NOT NULL CHECK (epoch > 0),
  provider_slot_id uuid NOT NULL,
  reservation_id uuid NOT NULL UNIQUE REFERENCES budget_reservations(id),
  request_hash text NOT NULL CHECK (request_hash ~ '^[0-9a-f]{64}$'),
  request_body jsonb NOT NULL CHECK (pg_column_size(request_body) <= 262144),
  state text NOT NULL DEFAULT 'prepared' CHECK (state IN
    ('prepared','sending','response_saved','processed','unknown','failed')),
  response_hash text CHECK (response_hash IS NULL OR response_hash ~ '^[0-9a-f]{64}$'),
  response_body jsonb CHECK (response_body IS NULL OR pg_column_size(response_body) <= 1048576),
  stop_reason text CHECK (stop_reason IS NULL OR length(stop_reason) <= 100),
  usage_tokens bigint CHECK (usage_tokens IS NULL OR usage_tokens >= 0),
  usage_tools bigint CHECK (usage_tools IS NULL OR usage_tools >= 0),
  created_at timestamptz NOT NULL DEFAULT clock_timestamp(),
  sending_at timestamptz,
  response_at timestamptz,
  processed_at timestamptz,
  UNIQUE(task_id,round_index),
  UNIQUE(request_id,task_id),
  CHECK ((state IN ('response_saved','processed')) = (response_hash IS NOT NULL AND response_body IS NOT NULL AND stop_reason IS NOT NULL)),
  CHECK ((state IN ('response_saved','processed')) = (response_at IS NOT NULL)),
  CHECK ((state='processed') = (processed_at IS NOT NULL))
);
CREATE INDEX provider_calls_recovery ON provider_calls(state,sending_at) WHERE state IN ('prepared','sending','unknown');
-- A task has at most one unresolved model round. In particular, `unknown`
-- blocks an automatic next request until reconciliation or operator handling.
CREATE UNIQUE INDEX one_open_provider_call_per_task ON provider_calls(task_id)
  WHERE state IN ('prepared','sending','response_saved','unknown');

CREATE FUNCTION reject_provider_call_identity_mutation() RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN
  IF (NEW.request_id,NEW.task_id,NEW.round_index,NEW.endpoint,NEW.release_id,NEW.model,NEW.owner,NEW.epoch,
      NEW.provider_slot_id,NEW.reservation_id,NEW.request_hash,NEW.request_body,NEW.created_at)
     IS DISTINCT FROM
     (OLD.request_id,OLD.task_id,OLD.round_index,OLD.endpoint,OLD.release_id,OLD.model,OLD.owner,OLD.epoch,
      OLD.provider_slot_id,OLD.reservation_id,OLD.request_hash,OLD.request_body,OLD.created_at) THEN
    RAISE EXCEPTION 'provider call identity is immutable';
  END IF;
  IF NOT (
    (OLD.state='prepared' AND NEW.state IN ('prepared','sending','failed')) OR
    (OLD.state='sending' AND NEW.state IN ('sending','response_saved','unknown','failed')) OR
    (OLD.state='unknown' AND NEW.state IN ('unknown','response_saved')) OR
    (OLD.state='response_saved' AND NEW.state IN ('response_saved','processed')) OR
    (OLD.state='processed' AND NEW.state='processed') OR
    (OLD.state='failed' AND NEW.state='failed')
  ) THEN
    RAISE EXCEPTION 'invalid provider call state transition';
  END IF;
  IF OLD.response_hash IS NOT NULL AND
     (NEW.response_hash,NEW.response_body,NEW.stop_reason,NEW.response_at)
       IS DISTINCT FROM (OLD.response_hash,OLD.response_body,OLD.stop_reason,OLD.response_at) THEN
    RAISE EXCEPTION 'provider response is immutable';
  END IF;
  IF OLD.usage_tokens IS NOT NULL AND NEW.usage_tokens IS DISTINCT FROM OLD.usage_tokens OR
     OLD.usage_tools IS NOT NULL AND NEW.usage_tools IS DISTINCT FROM OLD.usage_tools THEN
    RAISE EXCEPTION 'known provider usage is immutable';
  END IF;
  IF OLD.response_hash IS NOT NULL AND OLD.state IN ('response_saved','processed') AND
     NEW.state IN ('response_saved','processed') AND
     (NEW.usage_tokens IS NULL AND OLD.usage_tokens IS NOT NULL OR
      NEW.usage_tools IS NULL AND OLD.usage_tools IS NOT NULL) THEN
    RAISE EXCEPTION 'known provider usage cannot become unknown';
  END IF;
  RETURN NEW;
END;
$$;
CREATE TRIGGER immutable_provider_call_identity BEFORE UPDATE ON provider_calls
FOR EACH ROW EXECUTE FUNCTION reject_provider_call_identity_mutation();
