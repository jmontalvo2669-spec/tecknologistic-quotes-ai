"""Esquema de prompts/classifier_v1.txt y docs/agent_contracts.md §2."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class Classification(StrEnum):
    RFQ_NUEVA = "RFQ_NUEVA"
    ACLARACION = "ACLARACION"
    COTIZACION_ENVIADA = "COTIZACION_ENVIADA"
    PO_CLIENTE = "PO_CLIENTE"
    ABASTECIMIENTO_PROVEEDOR = "ABASTECIMIENTO_PROVEEDOR"
    SPAM_NO_RELEVANTE = "SPAM_NO_RELEVANTE"
    EXCEPCION = "EXCEPCION"


class ThreadContextMessage(BaseModel):
    subject: str
    summary: str


class ClassifierInput(BaseModel):
    subject: str
    body_text: str
    from_: str = Field(alias="from")
    attachment_names_and_types: list[str] = []
    thread_context: list[ThreadContextMessage] | None = None

    model_config = {"populate_by_name": True}


class EmailClassified(BaseModel):
    """Evento EMAIL_CLASSIFIED — producido por el Clasificador."""

    classification: Classification
    confidence: float = Field(ge=0.0, le=1.0)
    signals: list[str]
    requires_human_review: bool
    ambiguous_alternative: Classification | None = None
    model_used: str | None = None
    prompt_version: str = "classifier_v1"
