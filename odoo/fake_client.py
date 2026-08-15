"""Cliente Odoo falso — para pruebas y desarrollo, nunca conecta a un Odoo
real. Cumple odoo.client.OdooClient. Permite simular que la verificación
posterior a una escritura falla (test_extractor... test_odoo_connector
caso 18: "fallo después de escritura Odoo")."""

from __future__ import annotations

from typing import Any


class FakeOdooClient:
    def __init__(self, *, fail_verify_for: set[int] | None = None) -> None:
        self._records: dict[str, dict[int, dict[str, Any]]] = {}
        self._next_id = 1
        self._fail_verify_for = fail_verify_for or set()

    def read(self, model: str, record_id: int) -> dict[str, Any] | None:
        if record_id in self._fail_verify_for:
            return None
        return self._records.get(model, {}).get(record_id)

    def create(self, model: str, values: dict[str, Any]) -> int:
        record_id = self._next_id
        self._next_id += 1
        self._records.setdefault(model, {})[record_id] = dict(values)
        return record_id

    def write(self, model: str, record_id: int, values: dict[str, Any]) -> bool:
        if model not in self._records or record_id not in self._records[model]:
            return False
        self._records[model][record_id].update(values)
        return True
