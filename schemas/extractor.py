"""Esquema de prompts/extractor_v1.txt y docs/agent_contracts.md §3."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ExtractedLine(BaseModel):
    line_id: str
    description: str | None = None
    quantity: float | None = None
    unit: str | None = None
    manufacturer: str | None = None
    part_number: str | None = None
    standard: str | None = None
    specification: str | None = None
    observations: str | None = None


class DocumentExtracted(BaseModel):
    """Evento DOCUMENT_EXTRACTED — producido por el Extractor (código o IA)."""

    lines: list[ExtractedLine]
    line_count_confidence: float = Field(ge=0.0, le=1.0)
    ambiguous_groupings: list[str] = []
    requires_human_review: bool
    source: str = Field(
        description="'code' (pandas/openpyxl/texto) o 'claude' (prompts/extractor_v1.txt)"
    )
    prompt_version: str | None = None
