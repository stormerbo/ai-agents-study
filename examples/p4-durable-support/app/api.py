"""Task API; all data access is scoped to the current authenticated owner."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request, Response

from .auth import authenticate
from .db import connect, create_task, owned_task
from .models import ErrorResponse, EventPage, TaskCreate, TaskView

router = APIRouter()
ERRORS = {code: {"model": ErrorResponse} for code in (401, 403, 404, 409, 422, 503)}


def authorized_connection(request: Request, authorization: Annotated[str | None, Header()] = None):
    # Authenticate before connecting so bogus tokens remain 401 during DB outages.
    from .auth import bearer_identity
    bearer_identity(authorization)
    with connect(request.app.state.settings.database_url) as conn:
        principal = authenticate(conn, authorization)
        yield conn, principal


@router.post("/v1/tasks", response_model=TaskView, status_code=201, responses={200: {"model": TaskView}, **ERRORS})
def submit_task(payload: TaskCreate, response: Response,
                idempotency_key: Annotated[str, Header(min_length=1, max_length=200)],
                context=Depends(authorized_connection, scope="function")):
    conn, principal = context
    row, created = create_task(conn, principal, idempotency_key, payload)
    response.status_code = 201 if created else 200
    response.headers["Location"] = f"/v1/tasks/{row['id']}"
    return row


@router.get("/v1/tasks/{task_id}", response_model=TaskView, responses=ERRORS)
def read_task(task_id: UUID, context=Depends(authorized_connection, scope="function")):
    conn, principal = context
    return owned_task(conn, principal, task_id)


@router.get("/v1/tasks/{task_id}/events", response_model=EventPage, responses=ERRORS)
def read_events(task_id: UUID, after: Annotated[int, Query(ge=0)] = 0,
                limit: Annotated[int, Query(ge=1, le=100)] = 100,
                context=Depends(authorized_connection, scope="function")):
    conn, principal = context
    owned_task(conn, principal, task_id)
    rows = conn.execute("SELECT seq,kind,payload,redaction_version,created_at FROM events WHERE task_id=%s AND seq>%s ORDER BY seq LIMIT %s",
                        (task_id, after, limit)).fetchall()
    return {"events": rows, "next_after": rows[-1]["seq"] if rows else after}


@router.get("/v1/tasks/{task_id}/approvals", responses={501: {"model": ErrorResponse}, **ERRORS})
def read_approvals(task_id: UUID, context=Depends(authorized_connection, scope="function")):
    """Reserve an authorization boundary; Task 2 supplies the actual workflow."""
    conn, principal = context
    owned_task(conn, principal, task_id)
    raise HTTPException(501, detail={"code": "approvals_unavailable", "message": "Approval workflow is not implemented in Task 1"})
