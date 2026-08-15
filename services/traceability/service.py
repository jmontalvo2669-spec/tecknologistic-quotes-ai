"""Agente 9 — Trazabilidad (docs/agent_contracts.md §9, sección 17 de
docs/architecture.md). Cruza Gmail ↔ Expediente ↔ Odoo y calcula
completeness_score + gaps[]."""

from __future__ import annotations

from schemas.traceability import TraceabilityResult


def compute_completeness(case_id: str, checks: dict[str, bool]) -> TraceabilityResult:
    """`checks` es {nombre_del_artefacto_esperado: presente_o_no}. Genérico
    a propósito: qué artefactos aplican depende del estado del expediente
    (ver p0_checks() para el subconjunto P0)."""

    if not checks:
        return TraceabilityResult(
            case_id=case_id, completeness_score=0.0, gaps=["no hay checks definidos para este expediente"]
        )

    gaps = [name for name, present in checks.items() if not present]
    completeness_score = (len(checks) - len(gaps)) / len(checks)
    return TraceabilityResult(case_id=case_id, completeness_score=completeness_score, gaps=gaps)


def p0_checks(
    *,
    correo_ingerido: bool,
    lineas_extraidas: bool,
    expediente_resuelto: bool,
    cotizador_asignado: bool,
) -> dict[str, bool]:
    """Artefactos del flujo P0 (EMAIL → EXPEDIENTE → EXTRACCIÓN → CONTEO →
    BALANCEO, sección 37 de docs/architecture.md). Los artefactos de Odoo
    (P1) se agregan cuando el connector real exista."""

    return {
        "correo_ingerido": correo_ingerido,
        "lineas_extraidas": lineas_extraidas,
        "expediente_resuelto": expediente_resuelto,
        "cotizador_asignado": cotizador_asignado,
    }
