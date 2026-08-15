"""Evento de auditoría de transición — regla general #3 de docs/state_machine.md."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class AuditEvent(BaseModel):
    case_id: str
    estado_origen: str | None
    estado_destino: str
    evento: str
    agente_actor: str
    timestamp: datetime
    motivo: str
    correlation_id: str
