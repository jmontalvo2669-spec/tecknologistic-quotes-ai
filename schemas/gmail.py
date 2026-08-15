"""Esquema de docs/agent_contracts.md §1 — Gmail Ingest."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, Field


class Attachment(BaseModel):
    filename: str
    mime_type: str
    storage_path: str
    sha256: str


class EmailIngested(BaseModel):
    """Evento EMAIL_INGESTED — producido por Gmail Ingest."""

    case_hint_id: str | None = None
    gmail_message_id: str
    gmail_thread_id: str
    message_id_header: str
    in_reply_to: str | None = None
    references: list[str] = []
    from_: str = Field(alias="from")
    to: list[str] = []
    cc: list[str] = []
    subject: str
    date: datetime
    body_text: str
    attachments: list[Attachment] = []
    message_hash: str

    model_config = {"populate_by_name": True}
