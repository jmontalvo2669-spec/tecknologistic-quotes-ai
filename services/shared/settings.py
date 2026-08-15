"""Configuración centralizada — variables de .env.example.

Todo umbral de confianza es una constante configurable con valor numérico
por defecto (regla 20 de docs/architecture.md §3) — nunca una condición
cualitativa sin número en el código. Los valores sin default conocido
quedan `None` explícitamente: no se inventan (regla 17).
"""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Umbrales de confianza (defaults ya definidos en docs/architecture.md)
    classifier_escalation_threshold: float = 0.80
    classifier_min_threshold: float = 0.60
    line_count_confidence_threshold: float = 0.90
    case_resolver_min_confidence: float = 0.75
    technical_normalizer_min_confidence: float = 0.85

    # Orquestador (docs/orchestrator_decision_logic.md)
    max_retries: int = 3
    clarification_wait_hours: int = 24

    # Gobierno de costo de IA — sin techo fijado todavía (open_questions.md A.7)
    ai_cost_budget_per_case_usd: float | None = None

    # Privacidad — sin valor todavía (open_questions.md A.5)
    data_retention_days: int | None = None

    # Modelos de Claude — nombres reales pendientes de decidir con Jorge
    claude_model_fast: str | None = None
    claude_model_reasoning: str | None = None


settings = Settings()
