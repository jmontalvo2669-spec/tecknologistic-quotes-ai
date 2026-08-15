"""Agente 6 — Orquestador: flujo P0 feliz "EMAIL → EXPEDIENTE → EXTRACCIÓN →
CONTEO → BALANCEO" (sección 37 de docs/architecture.md), con mocks/fixtures
(PASO 6). Aplica docs/state_machine.md literalmente vía
services/workflow/state_machine.py — ninguna transición se ejecuta sin
pasar por find_transition().

Este es el primer objetivo de implementación, no el Orquestador completo:
cubre el camino feliz de una RFQ_NUEVA de un thread nuevo. Los puntos de
decisión D1-D5 de docs/orchestrator_decision_logic.md (reintentos,
escalamiento, aclaración al cliente, notificaciones, reasignación) no están
implementados todavía — quedan para cuando haya un event bus/scheduler real
que los dispare.
"""

from __future__ import annotations

import datetime as dt
import uuid
from dataclasses import dataclass

from gmail.client import GmailClient
from schemas.balancer import BalancerInput, CotizadorRoster, RosterFlags
from schemas.classifier import ClassifierInput, ThreadContextMessage
from schemas.classifier import EmailClassified
from schemas.extractor import DocumentExtracted
from schemas.balancer import RfqAssigned
from schemas.traceability import TraceabilityResult
from services.classifier.service import classify
from services.extractor.service import extract
from services.gmail_ingest.service import ingest
from services.shared.blob_store import InMemoryBlobStore
from services.shared.claude_client import ClaudeClient
from services.shared.repositories import InMemoryExpedienteRepository, InMemoryIngestedMessageRepository
from services.shared.settings import Settings, settings as default_settings
from services.traceability.service import compute_completeness, p0_checks
from services.workflow.state_machine import EstadoExpediente, TransitionRejected, find_transition
from services.workload_balancer.service import assign


@dataclass
class P0PipelineResult:
    case_id: str | None
    estado_final: EstadoExpediente | None
    classification: EmailClassified | None
    extraction: DocumentExtracted | None
    assignment: RfqAssigned | None
    traceability: TraceabilityResult | None
    duplicate: bool = False


def _registrar_transicion(
    *,
    expediente_repo: InMemoryExpedienteRepository,
    case_id: str,
    estado_actual: EstadoExpediente | None,
    evento: str,
    condition_tag: str,
    agente_override: str | None = None,
) -> EstadoExpediente:
    transition = find_transition(estado_actual, evento, condition_tag)
    correlation_id = str(uuid.uuid4())
    expediente_repo.record_transition(
        case_id=case_id,
        estado_origen=str(estado_actual) if estado_actual else None,
        estado_destino=str(transition.destino),
        evento=evento,
        agente_actor=agente_override or transition.actor,
        motivo=transition.condicion_texto,
        correlation_id=correlation_id,
        timestamp=dt.datetime.now(dt.timezone.utc),
    )
    return transition.destino


def run_p0_happy_path(
    gmail_message_id: str,
    *,
    gmail_client: GmailClient,
    claude_client: ClaudeClient,
    ingest_repo: InMemoryIngestedMessageRepository,
    expediente_repo: InMemoryExpedienteRepository,
    blob_store: InMemoryBlobStore,
    roster: list[CotizadorRoster],
    flags: RosterFlags | None = None,
    config: Settings = default_settings,
) -> P0PipelineResult:
    # 1) Gmail Ingest
    ingested = ingest(gmail_message_id, client=gmail_client, repo=ingest_repo, blob_store=blob_store)
    if ingested is None:
        return P0PipelineResult(None, None, None, None, None, None, duplicate=True)

    # Fila 1: (ninguno) -> RECIBIDA
    year = ingested.date.year
    case_id = expediente_repo.next_case_id(year)
    expediente_repo.create(case_id, ingested.gmail_thread_id, str(EstadoExpediente.RECIBIDA))
    ingest_repo.link_case_to_thread(ingested.gmail_thread_id, case_id)
    estado = _registrar_transicion(
        expediente_repo=expediente_repo, case_id=case_id, estado_actual=None,
        evento="EMAIL_INGESTED", condition_tag="new_message_not_duplicate",
    )

    # 2) Clasificador
    classification = classify(
        ClassifierInput(
            subject=ingested.subject,
            body_text=ingested.body_text,
            **{"from": ingested.from_},
            attachment_names_and_types=[a.filename for a in ingested.attachments],
            thread_context=None,
        ),
        client=claude_client,
        config=config,
    )
    condition_tag = "requires_human_review" if classification.requires_human_review else "ok"
    estado = _registrar_transicion(
        expediente_repo=expediente_repo, case_id=case_id, estado_actual=estado,
        evento="EMAIL_CLASSIFIED", condition_tag=condition_tag,
    )
    if classification.requires_human_review:
        return P0PipelineResult(case_id, estado, classification, None, None, None)

    # 3) Extractor (usa el primer adjunto — asume Excel para el camino feliz P0)
    assert ingested.attachments, "el camino feliz P0 espera al menos un adjunto"
    attachment = ingested.attachments[0]
    content = blob_store.get(attachment.storage_path)
    assert content is not None
    extraction = extract(document_type="excel", content=content, config=config)

    if not extraction.lines:
        estado = _registrar_transicion(
            expediente_repo=expediente_repo, case_id=case_id, estado_actual=estado,
            evento="DOCUMENT_EXTRACTED", condition_tag="extraction_failed",
        )
        return P0PipelineResult(case_id, estado, classification, extraction, None, None)

    condition_tag = "low_line_count_confidence" if extraction.requires_human_review else "ok"
    estado = _registrar_transicion(
        expediente_repo=expediente_repo, case_id=case_id, estado_actual=estado,
        evento="DOCUMENT_EXTRACTED", condition_tag=condition_tag,
    )
    if extraction.requires_human_review:
        return P0PipelineResult(case_id, estado, classification, extraction, None, None)

    # 4) Resolución de expediente: thread nuevo, sin candidatos -> es este
    # mismo case_id recién creado, confirmado por regla determinista.
    estado = _registrar_transicion(
        expediente_repo=expediente_repo, case_id=case_id, estado_actual=estado,
        evento="CASE_RESOLVED", condition_tag="case_unique_confirmed",
        agente_override="reglas deterministas (expediente recién creado, sin candidatos)",
    )

    # 5) Balanceador
    assignment = assign(
        BalancerInput(
            case_id=case_id,
            line_count=len(extraction.lines),
            cliente=ingested.from_,
            flags=flags or RosterFlags(),
            roster=roster,
        )
    )
    condition_tag = "no_cotizador_eligible" if assignment.cotizador_id is None else "cotizador_found"
    estado = _registrar_transicion(
        expediente_repo=expediente_repo, case_id=case_id, estado_actual=estado,
        evento="RFQ_ASSIGNED", condition_tag=condition_tag,
    )

    record = expediente_repo.get(case_id)
    record.cotizador_asignado = assignment.cotizador_id
    record.carga_antes = assignment.carga_antes
    record.carga_despues = assignment.carga_despues

    traceability = compute_completeness(
        case_id,
        p0_checks(
            correo_ingerido=True,
            lineas_extraidas=bool(extraction.lines),
            expediente_resuelto=True,
            cotizador_asignado=assignment.cotizador_id is not None,
        ),
    )

    return P0PipelineResult(case_id, estado, classification, extraction, assignment, traceability)
