CREATE TABLE final_outputs (
  task_id uuid PRIMARY KEY REFERENCES tasks(id),
  output jsonb NOT NULL,
  output_hash text NOT NULL CHECK (output_hash ~ '^[0-9a-f]{64}$'),
  execution_epoch bigint NOT NULL CHECK (execution_epoch>0),
  created_at timestamptz NOT NULL DEFAULT clock_timestamp()
);
CREATE TRIGGER immutable_final_outputs
 BEFORE UPDATE OR DELETE OR TRUNCATE ON final_outputs
 FOR EACH STATEMENT EXECUTE FUNCTION reject_event_mutation();
