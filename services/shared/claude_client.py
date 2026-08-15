"""Abstracción del cliente de Claude API.

Regla 22 de docs/architecture.md §3: todo uso de Claude API debe declarar
explícitamente qué modelo se usa y por qué. Regla 19: no gastar presupuesto
real de Claude API en volumen sin aprobación de GATE 1. Por eso:

- `ClaudeClient` es el Protocol que cualquier implementación debe cumplir.
- `FakeClaudeClient` es lo único que se usa en PASO 6 — nunca llama a la API
  real, siempre devuelve respuestas canned/deterministas provistas por el
  test o servicio que lo construye.
- `UnconfiguredClaudeClient` es el valor por defecto si alguien intenta usar
  un servicio sin inyectar explícitamente un cliente: falla ruidosamente en
  vez de intentar conectar a la API real por accidente.
"""

from __future__ import annotations

from typing import Callable, Protocol


class ClaudeClient(Protocol):
    def complete_json(
        self,
        *,
        prompt_version: str,
        system_prompt: str,
        input_payload: dict,
        model: str | None,
    ) -> dict: ...


ClaudeHandler = Callable[[str, dict, str | None], dict]


class FakeClaudeClient:
    """Cliente de prueba: delega en `handler(prompt_version, input_payload,
    model) -> dict`. No hace ninguna llamada de red."""

    def __init__(self, handler: ClaudeHandler) -> None:
        self._handler = handler
        self.calls: list[tuple[str, dict, str | None]] = []

    def complete_json(
        self,
        *,
        prompt_version: str,
        system_prompt: str,
        input_payload: dict,
        model: str | None,
    ) -> dict:
        self.calls.append((prompt_version, input_payload, model))
        return self._handler(prompt_version, input_payload, model)


class UnconfiguredClaudeClient:
    """Se usa cuando nadie inyectó un cliente real ni uno falso — falla
    explícitamente en vez de intentar gastar presupuesto real de Claude API
    sin aprobación de GATE 1."""

    def complete_json(self, **_kwargs) -> dict:
        raise RuntimeError(
            "No hay un ClaudeClient configurado. No se debe conectar la API "
            "real de Claude sin aprobación explícita de GATE 1 "
            "(docs/architecture.md §6). Inyecta un FakeClaudeClient para "
            "pruebas/desarrollo."
        )
