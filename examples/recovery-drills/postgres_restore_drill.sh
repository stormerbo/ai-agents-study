#!/usr/bin/env bash
set -Eeuo pipefail

image="${POSTGRES_IMAGE:-postgres:18.0-bookworm}"
prefix="agent-study-restore-$(date +%s)-$$"
app_source="${prefix}-app-source"
sink_source="${prefix}-sink-source"
app_target="${prefix}-app-target"
sink_target="${prefix}-sink-target"
workdir="$(mktemp -d)"

cleanup() {
  docker rm -f "$app_source" "$sink_source" "$app_target" "$sink_target" >/dev/null 2>&1 || true
  rm -rf "$workdir"
}
trap cleanup EXIT

start_postgres() {
  local name="$1"
  docker run -d --rm --name "$name" \
    -e POSTGRES_PASSWORD=drill-only \
    "$image" >/dev/null
  for attempt in $(seq 1 40); do
    if docker exec "$name" pg_isready -U postgres >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
  done
  printf 'PostgreSQL startup timed out: %s\n' "$name" >&2
  return 1
}

start_postgres "$app_source"
start_postgres "$sink_source"
docker exec "$app_source" createdb -U postgres appdb
docker exec "$sink_source" createdb -U postgres sinkdb

docker exec "$app_source" psql -v ON_ERROR_STOP=1 -U postgres -d appdb -c "
  CREATE TABLE tasks(task_id text PRIMARY KEY, status text NOT NULL);
  CREATE TABLE actions(action_id text PRIMARY KEY, status text NOT NULL, operation_id text NOT NULL);
  CREATE TABLE outbox(operation_id text PRIMARY KEY, status text NOT NULL);
  CREATE TABLE events(task_id text NOT NULL, seq integer NOT NULL, kind text NOT NULL, PRIMARY KEY(task_id, seq));
  INSERT INTO tasks VALUES ('task-1', 'reconciling');
  INSERT INTO actions VALUES ('action-1', 'unknown', 'op-1');
  INSERT INTO outbox VALUES ('op-1', 'unknown');
  INSERT INTO events VALUES ('task-1', 1, 'external_effect_unknown');
" >/dev/null

docker exec "$sink_source" psql -v ON_ERROR_STOP=1 -U postgres -d sinkdb -c "
  CREATE TABLE deliveries(operation_id text PRIMARY KEY, delivered_at timestamptz NOT NULL);
  INSERT INTO deliveries VALUES ('op-1', now());
" >/dev/null

docker exec "$app_source" pg_dump -Fc -U postgres appdb > "$workdir/appdb.dump"
docker exec "$sink_source" pg_dump -Fc -U postgres sinkdb > "$workdir/sinkdb.dump"
docker rm -f "$app_source" "$sink_source" >/dev/null

start_postgres "$app_target"
start_postgres "$sink_target"
docker exec "$app_target" createdb -U postgres restored_appdb
docker exec "$sink_target" createdb -U postgres restored_sinkdb
docker exec -i "$app_target" pg_restore --exit-on-error -U postgres -d restored_appdb < "$workdir/appdb.dump"
docker exec -i "$sink_target" pg_restore --exit-on-error -U postgres -d restored_sinkdb < "$workdir/sinkdb.dump"

app_state="$(docker exec "$app_target" psql -Aqt -U postgres -d restored_appdb -c "
  SELECT t.status || ':' || a.status || ':' || o.status || ':' || e.kind
  FROM tasks t
  JOIN actions a ON a.action_id = 'action-1'
  JOIN outbox o ON o.operation_id = a.operation_id
  JOIN events e ON e.task_id = t.task_id
  WHERE t.task_id = 'task-1' AND e.seq = 1;
")"
sink_count="$(docker exec "$sink_target" psql -Aqt -U postgres -d restored_sinkdb -c "
  SELECT count(*) FROM deliveries WHERE operation_id = 'op-1';
")"
test "$app_state" = 'reconciling:unknown:unknown:external_effect_unknown'
test "$sink_count" = '1'
printf 'RESTORE_OK app_state=%s sink_operation_count=%s image=%s\n' \
  "$app_state" "$sink_count" "$image"
