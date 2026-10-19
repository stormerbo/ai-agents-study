"""Versioned API payloads. Identity fields are deliberately absent."""
from datetime import datetime
import json
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class TaskCreate(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    prompt: str = Field(min_length=1, max_length=8000)
    release_id: str = Field(default="stage4-local-v1", min_length=1, max_length=100)


def canonical_payload(payload: TaskCreate) -> str:
    return json.dumps(payload.model_dump(mode="json"), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


class TaskView(BaseModel):
    id: UUID
    tenant_id: str
    owner_id: str
    status: Literal["queued", "running", "waiting_approval", "reconciling", "completed", "failed", "cancelled"]
    state_version: int
    release_id: str
    created_at: datetime


class EventView(BaseModel):
    seq: int
    kind: str
    payload: dict[str, Any]
    redaction_version: str
    created_at: datetime


class EventPage(BaseModel):
    events: list[EventView]
    next_after: int


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail
