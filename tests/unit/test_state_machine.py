import pytest

from services.workflow.state_machine import (
    TRANSITIONS,
    EstadoExpediente,
    TransitionRejected,
    find_transition,
    resolve_exception,
)


@pytest.mark.parametrize("transition", TRANSITIONS, ids=lambda t: f"fila_{t.row}")
def test_cada_fila_de_la_tabla_es_encontrable(transition):
    """Cada una de las 25 filas de docs/state_machine.md debe poder
    resolverse con su propio (origen, evento, condition_tag)."""
    if transition.row == 24:
        # Fila 24 tiene destino dinámico — se prueba aparte con resolve_exception().
        pytest.skip("fila 24 se prueba vía test_fila_24_resolucion_de_excepcion")

    estado_actual = None if transition.origen.__class__.__name__ == "_Ninguno" else (
        EstadoExpediente.ASIGNADA if transition.row == 25 else transition.origen
    )

    encontrada = find_transition(estado_actual, transition.evento, transition.condition_tag)
    assert encontrada.row == transition.row
    assert encontrada.destino == transition.destino


def test_fila_1_creacion_de_expediente():
    t = find_transition(None, "EMAIL_INGESTED", "new_message_not_duplicate")
    assert t.destino == EstadoExpediente.RECIBIDA


def test_fila_25_cualquier_estado_activo_escala_a_excepcion():
    for estado in EstadoExpediente:
        if estado in (EstadoExpediente.CERRADA, EstadoExpediente.EXCEPCION):
            continue
        t = find_transition(estado, "EXCEPTION_CREATED", "unrecoverable_error_or_sla_breach")
        assert t.destino == EstadoExpediente.EXCEPCION


def test_fila_25_no_aplica_desde_cerrada_ni_desde_excepcion():
    for estado in (EstadoExpediente.CERRADA, EstadoExpediente.EXCEPCION):
        with pytest.raises(TransitionRejected):
            find_transition(estado, "EXCEPTION_CREATED", "unrecoverable_error_or_sla_breach")


def test_fila_24_resolucion_de_excepcion_destino_lo_decide_el_humano():
    t = resolve_exception(EstadoExpediente.LISTA_PARA_ASIGNAR)
    assert t.row == 24
    assert t.origen == EstadoExpediente.EXCEPCION
    assert t.destino == EstadoExpediente.LISTA_PARA_ASIGNAR


def test_fila_24_no_puede_reingresar_a_excepcion():
    with pytest.raises(TransitionRejected):
        resolve_exception(EstadoExpediente.EXCEPCION)


def test_evento_no_mapeado_se_rechaza_nunca_se_aplica_por_si_acaso():
    """Regla general #1 de docs/state_machine.md."""
    with pytest.raises(TransitionRejected):
        find_transition(EstadoExpediente.RECIBIDA, "EVENTO_INEXISTENTE", "ok")


def test_evento_valido_en_estado_equivocado_se_rechaza():
    # QUOTE_APPROVED (fila 15) solo aplica desde COTIZACION_EN_REVISION, no desde RECIBIDA.
    with pytest.raises(TransitionRejected):
        find_transition(EstadoExpediente.RECIBIDA, "QUOTE_APPROVED", "approved")


def test_no_hay_dos_filas_con_la_misma_clave_origen_evento_condition_tag():
    claves = set()
    for t in TRANSITIONS:
        clave = (repr(t.origen), t.evento, t.condition_tag)
        assert clave not in claves, f"clave duplicada: {clave}"
        claves.add(clave)
