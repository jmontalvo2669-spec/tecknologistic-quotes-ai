"""Esquema de prompts/case_resolver_v1.txt y docs/agent_contracts.md §4."""

from __future__ import annotations

from pydantic import BaseModel, Field

EXCEPCION = "EXCEPCION"


class CaseCandidate(BaseModel):
    case_id: str
    cliente: str
    resumen: str
    ultima_actividad: str
    señales: list[str] = Field(default_factory=list)


class DiscardedCandidate(BaseModel):
    case_id: str
    reason: str


class CaseResolved(BaseModel):
    """Evento CASE_RESOLVED — producido por Case Resolver o reglas deterministas."""

    resolution: str
    """`case_id` elegido, o el literal "EXCEPCION"."""

    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str]
    discarded_candidates: list[DiscardedCandidate] = []
    requires_human_review: bool
    resolved_by: str = Field(description="'deterministic_rule' o 'claude'")
    prompt_version: str | None = None
