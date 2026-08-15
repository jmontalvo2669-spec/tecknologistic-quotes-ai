"""Esquema de docs/agent_contracts.md §8 — SLA / Seguimiento."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class SlaEvent(BaseModel):
    case_id: str
    sla_type: str
    tiempo_transcurrido_horas: float
    umbral_horas: float
    accion: Literal["alerta", "excepcion"]
