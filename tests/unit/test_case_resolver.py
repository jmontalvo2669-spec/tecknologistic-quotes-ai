import pytest

from schemas.case_resolver import CaseCandidate
from services.case_resolver.service import resolve
from services.shared.claude_client import FakeClaudeClient


def _candidate(**overrides) -> CaseCandidate:
    defaults = dict(
        case_id="TQL-2026-000201",
        cliente="Cliente A",
        resumen='RFQ de bridas 6" ASTM A105, 3 líneas',
        ultima_actividad="hace 2 días",
        señales=["remitente coincide"],
    )
    defaults.update(overrides)
    return CaseCandidate(**defaults)


def test_caso_5_respuesta_en_thread_ya_vinculado_es_determinista():
    result = resolve(
        subject="RE: Cotización",
        body_text="¿cuándo llega?",
        from_="cliente@example.com",
        date="2026-08-10",
        known_case_id_for_thread="TQL-2026-000201",
        candidates=[],
    )

    assert result.resolution == "TQL-2026-000201"
    assert result.resolved_by == "deterministic_rule"
    assert result.confidence == 1.0
    assert result.requires_human_review is False


def test_caso_6_numero_de_expediente_mencionado_en_el_cuerpo_es_determinista():
    result = resolve(
        subject="Nueva consulta",
        body_text="Sobre el expediente TQL-2026-000201, ¿hay novedades?",
        from_="cliente@example.com",
        date="2026-08-10",
        known_case_id_for_thread=None,
        candidates=[_candidate(case_id="TQL-2026-000201"), _candidate(case_id="TQL-2026-000198", cliente="Cliente A")],
    )

    assert result.resolution == "TQL-2026-000201"
    assert result.resolved_by == "deterministic_rule"
    assert len(result.discarded_candidates) == 1
    assert result.discarded_candidates[0].case_id == "TQL-2026-000198"


def test_unico_candidato_tambien_pasa_por_claude():
    """Decisión de Jorge (docs/agent_contracts.md §4): incluso con un único
    candidato sin evidencia determinista, se verifica con Claude — nunca se
    asigna automático solo porque no hay otro candidato con quien
    confundirse."""

    def handler(prompt_version, payload, model):
        assert len(payload["candidatos"]) == 1
        return {
            "resolution": "TQL-2026-000201",
            "confidence": 0.93,
            "evidence": ["único candidato, contenido consistente con el resumen"],
            "discarded_candidates": [],
            "requires_human_review": False,
        }

    client = FakeClaudeClient(handler)
    result = resolve(
        subject="RE",
        body_text="cualquier cosa",
        from_="cliente@example.com",
        date="2026-08-10",
        known_case_id_for_thread=None,
        candidates=[_candidate()],
        client=client,
    )

    assert result.resolution == "TQL-2026-000201"
    assert result.resolved_by == "claude"
    assert len(client.calls) == 1


def test_unico_candidato_sin_cliente_claude_lanza_error():
    with pytest.raises(ValueError):
        resolve(
            subject="RE",
            body_text="cualquier cosa",
            from_="cliente@example.com",
            date="2026-08-10",
            known_case_id_for_thread=None,
            candidates=[_candidate()],
        )


def test_ejemplo_del_prompt_bridas_resuelto_por_claude():
    """Ejemplo de prompts/case_resolver_v1.txt."""

    def handler(prompt_version, payload, model):
        return {
            "resolution": "TQL-2026-000201",
            "confidence": 0.88,
            "evidence": ["el mensaje menciona 'bridas' explícitamente"],
            "discarded_candidates": [
                {"case_id": "TQL-2026-000198", "reason": "no menciona bridas ni ítems relacionados"}
            ],
            "requires_human_review": False,
        }

    client = FakeClaudeClient(handler)
    result = resolve(
        subject="RE: Cotización",
        body_text="¿cuándo llega la cotización de las bridas?",
        from_="cliente@example.com",
        date="2026-08-10",
        known_case_id_for_thread=None,
        candidates=[
            _candidate(case_id="TQL-2026-000201", resumen='RFQ de bridas 6" ASTM A105, 3 líneas'),
            _candidate(case_id="TQL-2026-000198", resumen="RFQ de válvulas y accesorios, 12 líneas"),
        ],
        client=client,
    )

    assert result.resolution == "TQL-2026-000201"
    assert result.resolved_by == "claude"
    assert len(result.discarded_candidates) == 1


def test_caso_19_expediente_ambiguo_no_adivina_va_a_excepcion():
    def handler(prompt_version, payload, model):
        return {
            "resolution": "EXCEPCION",
            "confidence": 0.50,
            "evidence": ["ambos candidatos tienen evidencia comparable"],
            "discarded_candidates": [
                {"case_id": "TQL-2026-000198", "reason": "evidencia comparable, no se puede descartar con certeza"}
            ],
            "requires_human_review": True,
        }

    client = FakeClaudeClient(handler)
    result = resolve(
        subject="RE",
        body_text="mensaje ambiguo",
        from_="cliente@example.com",
        date="2026-08-10",
        known_case_id_for_thread=None,
        candidates=[_candidate(case_id="TQL-2026-000201"), _candidate(case_id="TQL-2026-000198")],
        client=client,
    )

    assert result.resolution == "EXCEPCION"
    assert result.requires_human_review is True


def test_sin_candidatos_ni_thread_conocido_lanza_error_no_es_su_trabajo():
    with pytest.raises(ValueError):
        resolve(
            subject="algo",
            body_text="algo",
            from_="cliente@example.com",
            date="2026-08-10",
            known_case_id_for_thread=None,
            candidates=[],
        )
