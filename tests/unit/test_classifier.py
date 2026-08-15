from schemas.classifier import Classification, ClassifierInput
from services.classifier.service import classify
from services.shared.claude_client import FakeClaudeClient
from services.shared.settings import Settings


def _input(**overrides) -> ClassifierInput:
    defaults = dict(
        subject="Solicitud de cotización - válvulas API 6D",
        body_text="Favor cotizar 12 válvulas norma API 6D.",
        **{"from": "cliente@example.com"},
        attachment_names_and_types=[],
        thread_context=None,
    )
    defaults.update(overrides)
    return ClassifierInput(**defaults)


def test_ejemplo_1_rfq_nueva_alta_confianza_no_escala():
    """Ejemplo 1 de prompts/classifier_v1.txt."""

    def handler(prompt_version, payload, model):
        assert model == "fast-model"  # nunca debería pedir el modelo de razonamiento
        return {
            "classification": "RFQ_NUEVA",
            "confidence": 0.97,
            "signals": ["subject indica solicitud de cotización"],
            "requires_human_review": False,
            "ambiguous_alternative": None,
        }

    client = FakeClaudeClient(handler)
    config = Settings(claude_model_fast="fast-model", claude_model_reasoning="reasoning-model")

    result = classify(_input(), client=client, config=config)

    assert result.classification == Classification.RFQ_NUEVA
    assert result.requires_human_review is False
    assert len(client.calls) == 1  # no escaló


def test_ejemplo_3_caso_ambiguo_excepcion():
    """Ejemplo 3 de prompts/classifier_v1.txt: confidence 0.45 -> escala,
    sigue bajo -> requires_human_review forzado a true."""

    def handler(prompt_version, payload, model):
        return {
            "classification": "EXCEPCION",
            "confidence": 0.45,
            "signals": ["body pide aclaración de plazo", "adjunto con nombre ambiguo"],
            "requires_human_review": True,
            "ambiguous_alternative": "PO_CLIENTE",
        }

    client = FakeClaudeClient(handler)
    config = Settings(claude_model_fast="fast-model", claude_model_reasoning="reasoning-model")

    result = classify(_input(), client=client, config=config)

    assert result.classification == Classification.EXCEPCION
    assert result.requires_human_review is True
    assert len(client.calls) == 2  # escaló porque 0.45 < 0.80


def test_escala_a_reasoning_y_confianza_recupera_sin_forzar_revision():
    calls_confidence = iter([0.70, 0.88])

    def handler(prompt_version, payload, model):
        return {
            "classification": "RFQ_NUEVA",
            "confidence": next(calls_confidence),
            "signals": ["señal"],
            "requires_human_review": False,
            "ambiguous_alternative": None,
        }

    client = FakeClaudeClient(handler)
    config = Settings(claude_model_fast="fast-model", claude_model_reasoning="reasoning-model")

    result = classify(_input(), client=client, config=config)

    assert len(client.calls) == 2
    assert client.calls[1][2] == "reasoning-model"
    assert result.confidence == 0.88
    assert result.requires_human_review is False


def test_escala_y_sigue_bajo_umbral_minimo_fuerza_revision_humana():
    """Sección 9.1 de docs/architecture.md: si confidence < 0.60 incluso
    tras escalar, nunca asignar (requires_human_review se fuerza a true)."""
    calls_confidence = iter([0.65, 0.55])

    def handler(prompt_version, payload, model):
        return {
            "classification": "RFQ_NUEVA",
            "confidence": next(calls_confidence),
            "signals": ["señal débil"],
            "requires_human_review": False,  # el modelo no lo marcó, el sistema debe forzarlo
            "ambiguous_alternative": None,
        }

    client = FakeClaudeClient(handler)
    config = Settings(claude_model_fast="fast-model", claude_model_reasoning="reasoning-model")

    result = classify(_input(), client=client, config=config)

    assert result.confidence == 0.55
    assert result.requires_human_review is True
