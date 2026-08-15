"""Esquema de docs/agent_contracts.md §7 — Odoo Connector."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel


class OdooWriteResult(BaseModel):
    case_id: str
    odoo_model: str
    odoo_id: int | None
    operation: Literal["create", "update"]
    idempotency_key: str
    verified: bool
    error: str | None = None
