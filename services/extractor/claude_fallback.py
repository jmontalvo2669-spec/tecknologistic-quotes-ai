"""Respaldo de extracción vía prompts/extractor_v1.txt — solo cuando el
código (services/extractor/excel.py, o extracción de texto de PDF) no
resolvió con confianza suficiente, o el documento es una imagen (sección 11
de docs/architecture.md: "código primero, IA después").
"""

from __future__ import annotations

from schemas.extractor import DocumentExtracted, ExtractedLine
from services.shared.claude_client import ClaudeClient
from services.shared.prompts import load_prompt

PROMPT_VERSION = "extractor_v1"


def extract_with_claude(
    *,
    document_type: str,
    raw_content: str,
    context: str | None,
    client: ClaudeClient,
    model: str | None,
) -> DocumentExtracted:
    raw = client.complete_json(
        prompt_version=PROMPT_VERSION,
        system_prompt=load_prompt(PROMPT_VERSION),
        input_payload={
            "document_type": document_type,
            "raw_content": raw_content,
            "contexto": context,
        },
        model=model,
    )
    lines = [ExtractedLine(**line) for line in raw["lines"]]
    return DocumentExtracted(
        lines=lines,
        line_count_confidence=raw["line_count_confidence"],
        ambiguous_groupings=raw.get("ambiguous_groupings", []),
        requires_human_review=raw["requires_human_review"],
        source="claude",
        prompt_version=PROMPT_VERSION,
    )
