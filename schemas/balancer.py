"""Esquema de docs/agent_contracts.md §5 — Balanceador."""

from __future__ import annotations

from pydantic import BaseModel


class RosterFlags(BaseModel):
    """`producto_especializado` y `certificacion_requerida` existieron aquí
    hasta que Jorge confirmó que los 6 cotizadores pueden cotizar cualquier
    producto — no hay especialidades ni certificaciones diferenciadas en la
    práctica (docs/decisions/0001-balancer-flags-especializacion.md). Se
    quitaron del contrato en vez de dejarlas como campos muertos."""

    cliente_reservado: bool = False
    urgente_vip: bool = False


class CotizadorRoster(BaseModel):
    cotizador_id: str
    activo: bool
    carga_actual_lineas: int


class BalancerInput(BaseModel):
    case_id: str
    line_count: int
    cliente: str
    flags: RosterFlags
    roster: list[CotizadorRoster]


class RfqAssigned(BaseModel):
    """Evento RFQ_ASSIGNED — producido por el Balanceador."""

    case_id: str
    cotizador_id: str | None
    carga_antes: int | None
    lineas_nuevas: int
    carga_despues: int | None
    regla_utilizada: str
    motivo: str
    requires_human_review: bool
