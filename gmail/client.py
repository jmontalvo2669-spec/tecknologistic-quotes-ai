"""Interfaz que debe cumplir cualquier cliente de Gmail (real o falso).

La implementación real (Gmail API + Pub/Sub) se conecta solo tras GATE 1.
Hasta entonces, services/gmail_ingest usa gmail.fake_client.FakeGmailClient.
"""

from __future__ import annotations

from typing import Protocol

from gmail.models import RawGmailMessage


class GmailClient(Protocol):
    def get_raw_message(self, gmail_message_id: str) -> RawGmailMessage: ...
