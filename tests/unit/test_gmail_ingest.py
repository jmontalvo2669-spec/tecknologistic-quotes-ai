from datetime import datetime, timezone

from gmail.fake_client import FakeGmailClient
from gmail.models import RawGmailMessage
from services.gmail_ingest.service import ingest
from services.shared.repositories import InMemoryIngestedMessageRepository


def _make_message(**overrides) -> RawGmailMessage:
    defaults = dict(
        gmail_message_id="msg-1",
        gmail_thread_id="thread-1",
        message_id_header="<msg-1@mail.example.com>",
        from_="cliente@example.com",
        to=["cotizaciones.tecknologistic@tecknologistic.com"],
        subject="Solicitud de cotización - válvulas API 6D",
        date=datetime(2026, 8, 10, tzinfo=timezone.utc),
        body_text="Favor cotizar 12 válvulas norma API 6D.",
    )
    defaults.update(overrides)
    return RawGmailMessage(**defaults)


def test_ingesta_normal_produce_email_ingested():
    client = FakeGmailClient()
    client.add_message(_make_message())
    repo = InMemoryIngestedMessageRepository()

    event = ingest("msg-1", client=client, repo=repo)

    assert event is not None
    assert event.gmail_message_id == "msg-1"
    assert event.from_ == "cliente@example.com"
    assert event.case_hint_id is None
    assert repo.exists(event.message_hash)


def test_correo_duplicado_se_descarta_caso_4_del_test_strategy():
    """Caso 4 de docs/test_strategy.md: mismo gmail_message_id/message_hash
    enviado dos veces -> el segundo evento se descarta, no se reprocesa."""
    client = FakeGmailClient()
    client.add_message(_make_message())
    repo = InMemoryIngestedMessageRepository()

    primero = ingest("msg-1", client=client, repo=repo)
    segundo = ingest("msg-1", client=client, repo=repo)

    assert primero is not None
    assert segundo is None


def test_case_hint_id_usa_el_case_id_ya_vinculado_al_thread():
    client = FakeGmailClient()
    client.add_message(_make_message())
    repo = InMemoryIngestedMessageRepository()
    repo.link_case_to_thread("thread-1", "TQL-2026-000001")

    event = ingest("msg-1", client=client, repo=repo)

    assert event.case_hint_id == "TQL-2026-000001"
