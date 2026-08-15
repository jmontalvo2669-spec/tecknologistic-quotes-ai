"""Agente 5 — Balanceador (docs/agent_contracts.md §5, sección 13 de
docs/architecture.md). Least Loaded by Open Lines. Nunca divide una RFQ
(siempre se asigna line_count completo a un único cotizador_id o a
ninguno). Empate -> round-robin configurable.

Exclusiones (sección 13): si cualquiera de las flags de RosterFlags está
activa (cliente_reservado, urgente_vip), el contrato de
docs/agent_contracts.md §5 no incluye qué cotizador del roster cumple esa
condición especial — el roster solo trae
`cotizador_id/activo/carga_actual_lineas` — así que no hay forma de
filtrar por esa capacidad sin inventar un campo que no está en el
contrato. Por eso cualquier flag activa excluye la asignación automática
por completo (requires_human_review=True), en vez de intentar adivinar
cuál cotizador la cumple.

`producto_especializado` y `certificacion_requerida` existieron aquí hasta
que Jorge confirmó que los 6 cotizadores pueden cotizar cualquier producto
— no hay especialidad ni certificación que diferencie a uno de otro en la
práctica. Sin esa diferenciación, excluir la asignación automática no
protegía nada (no hay "cotizador correcto" que un humano deba elegir en su
lugar) — ver docs/decisions/0001-balancer-flags-especializacion.md. Se
quitaron del contrato en vez de dejarlas sin uso.
"""

from __future__ import annotations

from schemas.balancer import BalancerInput, RfqAssigned


def assign(
    input_data: BalancerInput,
    *,
    round_robin_counter: dict[str, int] | None = None,
) -> RfqAssigned:
    if round_robin_counter is None:
        round_robin_counter = {}

    active_flags = [name for name, value in input_data.flags.model_dump().items() if value]
    if active_flags:
        return RfqAssigned(
            case_id=input_data.case_id,
            cotizador_id=None,
            carga_antes=None,
            lineas_nuevas=input_data.line_count,
            carga_despues=None,
            regla_utilizada="exclusion_flag",
            motivo=f"excluido de asignación automática por flags activos: {', '.join(active_flags)}",
            requires_human_review=True,
        )

    elegibles = [c for c in input_data.roster if c.activo]
    if not elegibles:
        return RfqAssigned(
            case_id=input_data.case_id,
            cotizador_id=None,
            carga_antes=None,
            lineas_nuevas=input_data.line_count,
            carga_despues=None,
            regla_utilizada="sin_elegibles",
            motivo="roster vacío o ningún cotizador activo",
            requires_human_review=True,
        )

    min_carga = min(c.carga_actual_lineas for c in elegibles)
    empatados = [c for c in elegibles if c.carga_actual_lineas == min_carga]

    if len(empatados) == 1:
        elegido = empatados[0]
        regla = "least_loaded_by_open_lines"
        motivo = f"cotizador con menor carga ({elegido.carga_actual_lineas} líneas abiertas)"
    else:
        empatados_ordenados = sorted(
            empatados, key=lambda c: round_robin_counter.get(c.cotizador_id, 0)
        )
        elegido = empatados_ordenados[0]
        round_robin_counter[elegido.cotizador_id] = round_robin_counter.get(elegido.cotizador_id, 0) + 1
        regla = "least_loaded_by_open_lines+round_robin_tiebreak"
        motivo = (
            f"empate en {elegido.carga_actual_lineas} líneas abiertas entre "
            f"{len(empatados)} cotizadores, desempatado por round-robin"
        )

    return RfqAssigned(
        case_id=input_data.case_id,
        cotizador_id=elegido.cotizador_id,
        carga_antes=elegido.carga_actual_lineas,
        lineas_nuevas=input_data.line_count,
        carga_despues=elegido.carga_actual_lineas + input_data.line_count,
        regla_utilizada=regla,
        motivo=motivo,
        requires_human_review=False,
    )
