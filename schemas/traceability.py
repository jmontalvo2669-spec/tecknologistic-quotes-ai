"""Esquema de docs/agent_contracts.md §9 — Trazabilidad."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TraceabilityResult(BaseModel):
    case_id: str
    completeness_score: float = Field(ge=0.0, le=1.0)
    gaps: list[str] = []
