"""Agente 1 — Gmail Ingest (docs/agent_contracts.md §1, sección 9 de
docs/architecture.md).

Responsabilidades: recuperar mensaje, calcular hash, detectar duplicados,
publicar EMAIL_INGESTED. No sobrescribe archivos originales (aquí: no
sobrescribe el `storage_path` de un adjunto ya guardado).
"""

from __future__ import annotations

import hashlib

from gmail.client import GmailClient
from gmail.models import RawGmailMessage
from schemas.gmail import Attachment, EmailIngested
from services.shared.blob_store import InMemoryBlobStore
from services.shared.repositories import InMemoryIngestedMessageRepository


def _compute_message_hash(message: RawGmailMessage) -> str:
    payload = f"{message.gmail_message_id}|{message.subject}|{message.body_text}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def _store_attachment(gmail_message_id: str, raw, blob_store: InMemoryBlobStore | None) -> Attachment:
    sha256 = hashlib.sha256(raw.content).hexdigest()
    storage_path = f"mock-storage/{gmail_message_id}/{sha256}/{raw.filename}"
    if blob_store is not None:
        blob_store.put(storage_path, raw.content)
    return Attachment(
        filename=raw.filename,
        mime_type=raw.mime_type,
        storage_path=storage_path,
        sha256=sha256,
    )


def ingest(
    gmail_message_id: str,
    *,
    client: GmailClient,
    repo: InMemoryIngestedMessageRepository,
    blob_store: InMemoryBlobStore | None = None,
) -> EmailIngested | None:
    """Devuelve EmailIngested, o None si el mensaje ya fue ingerido
    (idempotencia — regla de contrato de docs/agent_contracts.md §1:
    'si existe, no reprocesar ni volver a publicar'). Si se pasa
    `blob_store`, los adjuntos se guardan ahí (nunca sobrescribe uno
    existente) para que el Extractor pueda recuperarlos por storage_path."""

    message = client.get_raw_message(gmail_message_id)
    message_hash = _compute_message_hash(message)

    if repo.exists(message_hash):
        return None

    case_hint_id = repo.case_hint_for_thread(message.gmail_thread_id)
    attachments = [_store_attachment(gmail_message_id, a, blob_store) for a in message.attachments]

    event = EmailIngested(
        case_hint_id=case_hint_id,
        gmail_message_id=message.gmail_message_id,
        gmail_thread_id=message.gmail_thread_id,
        message_id_header=message.message_id_header,
        in_reply_to=message.in_reply_to,
        references=message.references,
        **{"from": message.from_},
        to=message.to,
        cc=message.cc,
        subject=message.subject,
        date=message.date,
        body_text=message.body_text,
        attachments=attachments,
        message_hash=message_hash,
    )

    repo.save(message_hash=message_hash, gmail_thread_id=message.gmail_thread_id, case_id=case_hint_id)
    return event
