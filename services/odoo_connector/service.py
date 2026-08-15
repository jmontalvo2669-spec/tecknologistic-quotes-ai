"""Agente 7 — Odoo Connector (docs/agent_contracts.md §7, sección 15 de
docs/architecture.md). READ → DECIDE → VALIDATE → WRITE → VERIFY → AUDIT.

Nunca invocado directo por Claude — solo por el Orquestador tras aprobación
humana (sección 22/RACI). Nunca asume éxito silencioso: si la escritura
ocurre pero la verificación posterior falla, se reporta explícitamente
(caso 18 de docs/test_strategy.md), nunca se asume que sí se escribió.
"""

from __future__ import annotations

from schemas.odoo import OdooWriteResult
from odoo.client import OdooClient
from services.shared.repositories import InMemoryOdooIdempotencyStore

# "Modelos principales potenciales" — sección 15 de docs/architecture.md.
# Deben validarse contra la instancia real (Odoo 18, ver
# docs/open_questions.md A.3) antes de asumirlos definitivos.
KNOWN_ODOO_MODELS = frozenset(
    {
        "res.partner",
        "sale.order",
        "sale.order.line",
        "purchase.order",
        "purchase.order.line",
        "product.product",
        "product.template",
    }
)


class OdooModelNotValidated(Exception):
    """VALIDATE rechazó el modelo — no está en KNOWN_ODOO_MODELS. Nunca se
    escribe en un modelo no confirmado (regla 9 de docs/architecture.md §3:
    no escribir directamente sin validar)."""


def write_record(
    *,
    case_id: str,
    odoo_model: str,
    values: dict,
    idempotency_key: str,
    client: OdooClient,
    idempotency_store: InMemoryOdooIdempotencyStore,
) -> OdooWriteResult:
    # READ: ¿ya se escribió esto antes con esta idempotency_key?
    existing = idempotency_store.get(idempotency_key)

    # DECIDE: create si no existe, update si ya existe.
    operation = "update" if existing else "create"

    # VALIDATE
    if odoo_model not in KNOWN_ODOO_MODELS:
        raise OdooModelNotValidated(
            f"'{odoo_model}' no está en la lista de modelos validados contra Odoo 18 "
            f"(docs/open_questions.md A.3) — no se escribe sin confirmación explícita."
        )

    # WRITE
    if operation == "update":
        _model, odoo_id = existing
        client.write(odoo_model, odoo_id, values)
    else:
        odoo_id = client.create(odoo_model, values)
        idempotency_store.save(idempotency_key, odoo_model, odoo_id)

    # VERIFY: nunca asumir éxito silencioso.
    verified_record = client.read(odoo_model, odoo_id)
    verified = verified_record is not None

    # AUDIT: el llamador (Orquestador) es responsable de registrar este
    # resultado en el log de auditoría — este connector solo lo reporta.
    return OdooWriteResult(
        case_id=case_id,
        odoo_model=odoo_model,
        odoo_id=odoo_id if verified else odoo_id,
        operation=operation,
        idempotency_key=idempotency_key,
        verified=verified,
        error=None if verified else "escritura no verificada: VERIFY no encontró el registro tras WRITE",
    )
