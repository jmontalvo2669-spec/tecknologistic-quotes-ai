"""Representación cruda de un mensaje Gmail, tal como la devolvería la
Gmail API real (o, en PASO 6, el fixture/fake client)."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class RawAttachment:
    filename: str
    mime_type: str
    content: bytes


@dataclass
class RawGmailMessage:
    gmail_message_id: str
    gmail_thread_id: str
    message_id_header: str
    from_: str
    to: list[str]
    subject: str
    date: datetime
    body_text: str
    cc: list[str] = field(default_factory=list)
    in_reply_to: str | None = None
    references: list[str] = field(default_factory=list)
    attachments: list[RawAttachment] = field(default_factory=list)
