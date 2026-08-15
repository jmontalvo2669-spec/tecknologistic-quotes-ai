"""Prueba de extremo a extremo del primer objetivo de implementación
(sección 37 de docs/architecture.md): "EMAIL → EXPEDIENTE → EXTRACCIÓN →
CONTEO → BALANCEO", enteramente con mocks/fixtures — ningún sistema real.
"""

from datetime import datetime, timezone
from pathlib import Path

from gmail.fake_client import FakeGmailClient
from gmail.models import RawAttachment, RawGmailMessage
from schemas.balancer import CotizadorRoster
from services.shared.blob_store import InMemoryBlobStore
from services.shared.claude_client import FakeClaudeClient
from services.shared.repositories import InMemoryExpedienteRepository, InMemoryIngestedMessageRepository
from services.workflow.orchestrator import run_p0_happy_path
from services.workflow.state_machine import EstadoExpediente

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def _classifier_handler(prompt_version, payload, model):
    assert prompt_version == "classifier_v1"
    return {
        "classification": "RFQ_NUEVA",
        "confidence": 0.95,
        "signals": ["subject indica solicitud de cotización", "adjunto Excel de producto"],
        "requires_human_review": False,
        "ambiguous_alternative": None,
    }


def _make_message() -> RawGmailMessage:
    excel_bytes = (FIXTURES / "rfq_simple_1_linea.xlsx").read_bytes()
    return RawGmailMessage(
        gmail_message_id="msg-e2e-1",
        gmail_thread_id="thread-e2e-1",
        message_id_header="<msg-e2e-1@mail.example.com>",
        from_="cliente@example.com",
        to=["cotizaciones.tecknologistic@tecknologistic.com"],
        subject="Solicitud de cotización - válvulas API 6D",
        date=datetime(2026, 8, 10, tzinfo=timezone.utc),
        body_text="Favor cotizar según el Excel adjunto.",
        attachments=[RawAttachment(filename="rfq.xlsx", mime_type="application/vnd.ms-excel", content=excel_bytes)],
    )


def test_flujo_p0_completo_rfq_nueva_1_linea_se_asigna():
    gmail_client = FakeGmailClient()
    gmail_client.add_message(_make_message())
    claude_client = FakeClaudeClient(_classifier_handler)

    result = run_p0_happy_path(
        "msg-e2e-1",
        gmail_client=gmail_client,
        claude_client=claude_client,
        ingest_repo=InMemoryIngestedMessageRepository(),
        expediente_repo=InMemoryExpedienteRepository(),
        blob_store=InMemoryBlobStore(),
        roster=[
            CotizadorRoster(cotizador_id="cotizador-1", activo=True, carga_actual_lineas=2),
            CotizadorRoster(cotizador_id="cotizador-2", activo=True, carga_actual_lineas=9),
        ],
    )

    assert not result.duplicate
    assert result.case_id is not None and result.case_id.startswith("TQL-2026-")
    assert result.estado_final == EstadoExpediente.ASIGNADA
    assert result.classification.classification == "RFQ_NUEVA"
    assert len(result.extraction.lines) == 1
    assert result.assignment.cotizador_id == "cotizador-1"  # menor carga (2 < 9)
    assert result.traceability.completeness_score == 1.0
    assert result.traceability.gaps == []


def test_flujo_p0_correo_duplicado_no_reprocesa():
    gmail_client = FakeGmailClient()
    gmail_client.add_message(_make_message())
    claude_client = FakeClaudeClient(_classifier_handler)
    ingest_repo = InMemoryIngestedMessageRepository()
    expediente_repo = InMemoryExpedienteRepository()
    blob_store = InMemoryBlobStore()
    roster = [CotizadorRoster(cotizador_id="cotizador-1", activo=True, carga_actual_lineas=0)]

    primero = run_p0_happy_path(
        "msg-e2e-1", gmail_client=gmail_client, claude_client=claude_client,
        ingest_repo=ingest_repo, expediente_repo=expediente_repo, blob_store=blob_store, roster=roster,
    )
    segundo = run_p0_happy_path(
        "msg-e2e-1", gmail_client=gmail_client, claude_client=claude_client,
        ingest_repo=ingest_repo, expediente_repo=expediente_repo, blob_store=blob_store, roster=roster,
    )

    assert not primero.duplicate
    assert segundo.duplicate
