"""Orquesta el Agente 3 — Extractor: código primero, IA después (sección 11
de docs/architecture.md)."""

from __future__ import annotations

from schemas.extractor import DocumentExtracted
from services.extractor.claude_fallback import extract_with_claude
from services.extractor.excel import extract_from_excel_bytes
from services.shared.claude_client import ClaudeClient
from services.shared.settings import Settings, settings as default_settings


def extract(
    *,
    document_type: str,
    content: bytes | None = None,
    raw_content: str | None = None,
    context: str | None = None,
    client: ClaudeClient | None = None,
    config: Settings = default_settings,
) -> DocumentExtracted:
    if document_type == "excel":
        assert content is not None, "extracción de Excel requiere los bytes del archivo"
        result = extract_from_excel_bytes(content)
    else:
        assert client is not None, "documentos no estructurados requieren un ClaudeClient (fake en pruebas)"
        assert raw_content is not None
        result = extract_with_claude(
            document_type=document_type,
            raw_content=raw_content,
            context=context,
            client=client,
            model=config.claude_model_reasoning,
        )

    if result.line_count_confidence < config.line_count_confidence_threshold:
        result = result.model_copy(update={"requires_human_review": True})

    return result
