from schemas.balancer import BalancerInput, CotizadorRoster, RosterFlags
from services.workload_balancer.service import assign


def _input(roster: list[CotizadorRoster], **overrides) -> BalancerInput:
    defaults = dict(case_id="TQL-2026-000001", line_count=5, cliente="Cliente A", flags=RosterFlags())
    defaults.update(overrides)
    return BalancerInput(roster=roster, **defaults)


def test_asigna_al_cotizador_con_menor_carga():
    roster = [
        CotizadorRoster(cotizador_id="A", activo=True, carga_actual_lineas=10),
        CotizadorRoster(cotizador_id="B", activo=True, carga_actual_lineas=3),
        CotizadorRoster(cotizador_id="C", activo=True, carga_actual_lineas=7),
    ]
    result = assign(_input(roster))

    assert result.cotizador_id == "B"
    assert result.carga_antes == 3
    assert result.carga_despues == 8
    assert result.regla_utilizada == "least_loaded_by_open_lines"
    assert result.requires_human_review is False


def test_nunca_divide_la_rfq_lineas_nuevas_va_completo_a_un_solo_cotizador():
    roster = [CotizadorRoster(cotizador_id="A", activo=True, carga_actual_lineas=0)]
    result = assign(_input(roster, line_count=500))

    assert result.cotizador_id == "A"
    assert result.lineas_nuevas == 500
    assert result.carga_despues == 500


def test_caso_13_empate_de_carga_usa_round_robin():
    roster = [
        CotizadorRoster(cotizador_id="A", activo=True, carga_actual_lineas=5),
        CotizadorRoster(cotizador_id="B", activo=True, carga_actual_lineas=5),
    ]
    counter: dict[str, int] = {}

    primero = assign(_input(roster, case_id="TQL-2026-000001"), round_robin_counter=counter)
    segundo = assign(_input(roster, case_id="TQL-2026-000002"), round_robin_counter=counter)

    assert primero.cotizador_id != segundo.cotizador_id
    assert "round_robin" in primero.regla_utilizada


def test_caso_12_cotizador_ausente_unico_elegible_marcado_inactivo():
    roster = [CotizadorRoster(cotizador_id="A", activo=False, carga_actual_lineas=0)]
    result = assign(_input(roster))

    assert result.cotizador_id is None
    assert result.requires_human_review is True
    assert result.regla_utilizada == "sin_elegibles"


def test_roster_vacio_no_asigna_al_primero_disponible():
    result = assign(_input(roster=[]))

    assert result.cotizador_id is None
    assert result.requires_human_review is True


def test_flag_activa_excluye_asignacion_automatica_nunca_ignora_la_exclusion():
    roster = [CotizadorRoster(cotizador_id="A", activo=True, carga_actual_lineas=0)]
    result = assign(_input(roster, flags=RosterFlags(cliente_reservado=True)))

    assert result.cotizador_id is None
    assert result.requires_human_review is True
    assert "cliente_reservado" in result.motivo
