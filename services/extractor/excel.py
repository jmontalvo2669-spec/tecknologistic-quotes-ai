"""Extracción de líneas por código (Excel) — Agente 3, sección 11 de
docs/architecture.md. Código primero, IA después: este módulo nunca llama a
Claude, es el camino primario para Excel estructurado.

Regla de contrato (docs/agent_contracts.md §3): si la extracción fue 100%
por código, el output debe tener el MISMO esquema que produciría el prompt
(schemas.extractor.DocumentExtracted) para que el resto del sistema no
distinga el origen.
"""

from __future__ import annotations

import io
from typing import Any

import pandas as pd

from schemas.extractor import DocumentExtracted, ExtractedLine

_COLUMN_ALIASES: dict[str, tuple[str, ...]] = {
    "description": ("descripcion", "descripción", "description", "producto", "item"),
    "quantity": ("cantidad", "qty", "quantity"),
    "unit": ("unidad", "unit"),
    "manufacturer": ("fabricante", "manufacturer", "marca"),
    "part_number": ("part_number", "parte", "codigo", "código", "part number"),
    "standard": ("norma", "standard"),
    "specification": ("especificacion", "especificación", "specification", "spec"),
    "observations": ("observaciones", "observations", "notas"),
}

_REQUIRED_FOR_STRUCTURED_SHEET = ("description", "quantity")


def _normalize_header(value: Any) -> str:
    return str(value).strip().lower()


def _map_columns(headers: list[str]) -> dict[str, str]:
    """Devuelve {campo_canonico: nombre_de_columna_real} para las columnas
    reconocidas de esta hoja."""
    normalized = {h: _normalize_header(h) for h in headers}
    mapping: dict[str, str] = {}
    for canonical, aliases in _COLUMN_ALIASES.items():
        for header, norm in normalized.items():
            if norm in aliases:
                mapping[canonical] = header
                break
    return mapping


def _is_structured_sheet(mapping: dict[str, str]) -> bool:
    return all(field in mapping for field in _REQUIRED_FOR_STRUCTURED_SHEET)


def _pick_structured_sheet(sheets: dict[str, pd.DataFrame]) -> tuple[str, pd.DataFrame, dict[str, str]] | None:
    for name, df in sheets.items():
        mapping = _map_columns(list(df.columns))
        if _is_structured_sheet(mapping):
            return name, df, mapping
    return None


def _row_value(row: pd.Series, mapping: dict[str, str], field: str) -> str | None:
    if field not in mapping:
        return None
    value = row[mapping[field]]
    if pd.isna(value):
        return None
    text = str(value).strip()
    return text or None


def _merge_key(line: ExtractedLine) -> tuple:
    return (
        (line.description or "").strip().lower(),
        (line.unit or "").strip().lower(),
        (line.manufacturer or "").strip().lower(),
        (line.part_number or "").strip().lower(),
        (line.standard or "").strip().lower(),
        (line.specification or "").strip().lower(),
    )


def _merge_identical_lines(lines: list[ExtractedLine]) -> list[ExtractedLine]:
    """P0 crítica (sección 11 de docs/architecture.md): cantidades
    idénticas del mismo ítem son 1 línea, no N líneas. Solo fusiona cuando
    todas las filas del grupo tienen quantity explícito — si alguna es
    None, no se suman (no hay cómo inventar un total)."""

    merged: dict[tuple, ExtractedLine] = {}
    order: list[tuple] = []
    for line in lines:
        key = _merge_key(line)
        if key in merged and merged[key].quantity is not None and line.quantity is not None:
            merged[key] = merged[key].model_copy(
                update={"quantity": merged[key].quantity + line.quantity}
            )
        elif key in merged:
            # ya existe el grupo pero no se puede sumar con certeza -> se mantiene aparte
            order.append(key + (id(line),))
            merged[key + (id(line),)] = line
        else:
            merged[key] = line
            order.append(key)

    seen: list[ExtractedLine] = []
    for key in order:
        seen.append(merged[key])
    # re-numerar line_id secuencialmente tras la fusión
    return [line.model_copy(update={"line_id": str(i + 1)}) for i, line in enumerate(seen)]


def extract_from_excel_bytes(content: bytes) -> DocumentExtracted:
    sheets = pd.read_excel(io.BytesIO(content), sheet_name=None, dtype=object)

    picked = _pick_structured_sheet(sheets)
    if picked is None:
        return DocumentExtracted(
            lines=[],
            line_count_confidence=0.0,
            ambiguous_groupings=[
                "ninguna hoja tiene columnas reconocibles de descripción/cantidad"
            ],
            requires_human_review=True,
            source="code",
        )

    _sheet_name, df, mapping = picked

    raw_lines: list[ExtractedLine] = []
    for i, (_, row) in enumerate(df.iterrows()):
        description = _row_value(row, mapping, "description")
        if description is None:
            continue  # fila vacía/encabezado/separador — no se cuenta

        quantity_raw = _row_value(row, mapping, "quantity")
        quantity = float(quantity_raw) if quantity_raw is not None else None

        raw_lines.append(
            ExtractedLine(
                line_id=str(i + 1),
                description=description,
                quantity=quantity,
                unit=_row_value(row, mapping, "unit"),
                manufacturer=_row_value(row, mapping, "manufacturer"),
                part_number=_row_value(row, mapping, "part_number"),
                standard=_row_value(row, mapping, "standard"),
                specification=_row_value(row, mapping, "specification"),
                observations=_row_value(row, mapping, "observations"),
            )
        )

    lines = _merge_identical_lines(raw_lines)

    return DocumentExtracted(
        lines=lines,
        line_count_confidence=0.98 if lines else 0.0,
        ambiguous_groupings=[],
        requires_human_review=not lines,
        source="code",
    )
