"""Interfaz mínima que debe cumplir cualquier cliente de Odoo (real o falso).

La implementación real (Odoo External API) se conecta solo tras GATE 1 y
solo después de validar los modelos reales contra la instancia contratada
(sección 15 de docs/architecture.md, versión 18 confirmada en
docs/open_questions.md A.3 — sandbox todavía pendiente).
"""

from __future__ import annotations

from typing import Any, Protocol


class OdooClient(Protocol):
    def read(self, model: str, record_id: int) -> dict[str, Any] | None: ...

    def create(self, model: str, values: dict[str, Any]) -> int: ...

    def write(self, model: str, record_id: int, values: dict[str, Any]) -> bool: ...
