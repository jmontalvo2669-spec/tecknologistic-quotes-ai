"""Cliente Gmail falso — para pruebas y desarrollo con fixtures, nunca
conecta a Gmail real. Cumple gmail.client.GmailClient."""

from __future__ import annotations

from gmail.models import RawGmailMessage


class FakeGmailClient:
    def __init__(self, messages: dict[str, RawGmailMessage] | None = None) -> None:
        self._messages: dict[str, RawGmailMessage] = messages or {}

    def add_message(self, message: RawGmailMessage) -> None:
        self._messages[message.gmail_message_id] = message

    def get_raw_message(self, gmail_message_id: str) -> RawGmailMessage:
        try:
            return self._messages[gmail_message_id]
        except KeyError:
            raise LookupError(f"FakeGmailClient no tiene el mensaje {gmail_message_id!r}") from None
