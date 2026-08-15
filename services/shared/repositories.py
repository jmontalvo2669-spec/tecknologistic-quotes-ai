"""Repositorios en memoria — PASO 6 (mocks/fixtures, sin sistemas reales).

Cada repositorio expone la interfaz mínima que un repositorio respaldado
por Postgres real (services/shared/db_models.py + migrations/) tendría que
implementar. Swappear la implementación en memoria por una real es trabajo
de una fase posterior a GATE 1 — el resto de los servicios no debería
necesitar cambios si el reemplazo respeta esta interfaz.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from schemas.audit import AuditEvent


class InMemoryIngestedMessageRepository:
    """Idempotencia de Gmail Ingest — docs/agent_contracts.md §1."""

    def __init__(self) -> None:
        self._hashes: set[str] = set()
        # gmail_thread_id -> case_id, para poder ofrecer case_hint_id
        self._case_id_by_thread: dict[str, str] = {}

    def exists(self, message_hash: str) -> bool:
        return message_hash in self._hashes

    def save(self, *, message_hash: str, gmail_thread_id: str, case_id: str | None) -> None:
        self._hashes.add(message_hash)
        if case_id is not None:
            self._case_id_by_thread[gmail_thread_id] = case_id

    def case_hint_for_thread(self, gmail_thread_id: str) -> str | None:
        return self._case_id_by_thread.get(gmail_thread_id)

    def link_case_to_thread(self, gmail_thread_id: str, case_id: str) -> None:
        self._case_id_by_thread[gmail_thread_id] = case_id


class InMemoryOdooIdempotencyStore:
    """idempotency_key -> odoo_id ya escrito — evita duplicar create() ante
    reintentos (sección 20 de docs/architecture.md, docs/agent_contracts.md §7)."""

    def __init__(self) -> None:
        self._odoo_id_by_key: dict[str, tuple[str, int]] = {}

    def get(self, idempotency_key: str) -> tuple[str, int] | None:
        return self._odoo_id_by_key.get(idempotency_key)

    def save(self, idempotency_key: str, odoo_model: str, odoo_id: int) -> None:
        self._odoo_id_by_key[idempotency_key] = (odoo_model, odoo_id)


@dataclass
class ExpedienteRecord:
    case_id: str
    estado_actual: str
    gmail_thread_id: str
    cotizador_asignado: str | None = None
    carga_antes: int | None = None
    carga_despues: int | None = None
    transitions: list[AuditEvent] = field(default_factory=list)


class InMemoryExpedienteRepository:
    """Expedientes TQL + su historial de transiciones — sección 7 y regla
    general #3 de docs/state_machine.md."""

    def __init__(self) -> None:
        self._expedientes: dict[str, ExpedienteRecord] = {}
        self._sequence_by_year: dict[int, int] = {}

    def next_case_id(self, year: int) -> str:
        self._sequence_by_year[year] = self._sequence_by_year.get(year, 0) + 1
        return f"TQL-{year}-{self._sequence_by_year[year]:06d}"

    def create(self, case_id: str, gmail_thread_id: str, estado_actual: str) -> ExpedienteRecord:
        record = ExpedienteRecord(
            case_id=case_id, estado_actual=estado_actual, gmail_thread_id=gmail_thread_id
        )
        self._expedientes[case_id] = record
        return record

    def get(self, case_id: str) -> ExpedienteRecord | None:
        return self._expedientes.get(case_id)

    def record_transition(
        self,
        *,
        case_id: str,
        estado_origen: str | None,
        estado_destino: str,
        evento: str,
        agente_actor: str,
        motivo: str,
        correlation_id: str,
        timestamp,
    ) -> None:
        record = self._expedientes[case_id]
        record.estado_actual = estado_destino
        record.transitions.append(
            AuditEvent(
                case_id=case_id,
                estado_origen=estado_origen,
                estado_destino=estado_destino,
                evento=evento,
                agente_actor=agente_actor,
                timestamp=timestamp,
                motivo=motivo,
                correlation_id=correlation_id,
            )
        )
