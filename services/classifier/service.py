"""Agente 2 — Clasificador (prompts/classifier_v1.txt, docs/agent_contracts.md §2,
sección 9.1 de docs/architecture.md).

Escala de CLAUDE_MODEL_FAST a CLAUDE_MODEL_REASONING solo si
confidence < CLASSIFIER_ESCALATION_THRESHOLD; si sigue por debajo de
CLASSIFIER_MIN_THRESHOLD tras escalar, fuerza requires_human_review=true
(nunca cambia la clasificación en sí ni asigna con baja confianza).
"""

from __future__ import annotations

from schemas.classifier import ClassifierInput, EmailClassified
from services.shared.claude_client import ClaudeClient
from services.shared.prompts import load_prompt
from services.shared.settings import Settings, settings as default_settings

PROMPT_VERSION = "classifier_v1"


def _call_model(
    client: ClaudeClient, input_data: ClassifierInput, model: str | None
) -> EmailClassified:
    raw = client.complete_json(
        prompt_version=PROMPT_VERSION,
        system_prompt=load_prompt(PROMPT_VERSION),
        input_payload=input_data.model_dump(by_alias=True, mode="json"),
        model=model,
    )
    return EmailClassified(**raw, model_used=model, prompt_version=PROMPT_VERSION)


def classify(
    input_data: ClassifierInput,
    *,
    client: ClaudeClient,
    config: Settings = default_settings,
) -> EmailClassified:
    result = _call_model(client, input_data, config.claude_model_fast)

    if result.confidence < config.classifier_escalation_threshold:
        result = _call_model(client, input_data, config.claude_model_reasoning)
        if result.confidence < config.classifier_min_threshold:
            result = result.model_copy(update={"requires_human_review": True})

    return result
