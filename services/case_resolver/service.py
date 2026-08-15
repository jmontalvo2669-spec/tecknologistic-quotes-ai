"""Agente 4 — Case Resolver (prompts/case_resolver_v1.txt,
docs/agent_contracts.md §4, sección 12 de docs/architecture.md).

Orden de intento (sección 12): ID TQL, Gmail threadId, número de cotización,
PO cliente, referencias Odoo, remitente, referencias del contenido, señales
semánticas. Reglas deterministas primero; Claude solo para casos ambiguos.
Dos candidatos razonables -> NO ADIVINAR, EXCEPCION.
"""

from __future__ import annotations

import re

from schemas.case_resolver import CaseCandidate, CaseResolved, DiscardedCandidate
from services.shared.claude_client import ClaudeClient
from services.shared.prompts import load_prompt

PROMPT_VERSION = "case_resolver_v1"

CASE_ID_PATTERN = re.compile(r"TQL-\d{4}-\d{6}")


def resolve(
    *,
    subject: str,
    body_text: str,
    from_: str,
    date: str,
    known_case_id_for_thread: str | None,
    candidates: list[CaseCandidate],
    client: ClaudeClient | None = None,
    model: str | None = None,
) -> CaseResolved:
    # Regla determinista 1: el hilo de Gmail ya está vinculado a un expediente.
    if known_case_id_for_thread is not None:
        return CaseResolved(
            resolution=known_case_id_for_thread,
            confidence=1.0,
            evidence=["gmail_thread_id ya estaba vinculado a este expediente"],
            discarded_candidates=[],
            requires_human_review=False,
            resolved_by="deterministic_rule",
        )

    # Regla determinista 2: número de expediente mencionado explícitamente
    # en el texto y coincide con uno de los candidatos.
    match = CASE_ID_PATTERN.search(f"{subject} {body_text}")
    candidate_ids = {c.case_id for c in candidates}
    if match and match.group(0) in candidate_ids:
        resolved_id = match.group(0)
        return CaseResolved(
            resolution=resolved_id,
            confidence=0.95,
            evidence=[f"número de expediente {resolved_id} mencionado explícitamente en el mensaje"],
            discarded_candidates=[
                DiscardedCandidate(case_id=c.case_id, reason="no fue el expediente mencionado explícitamente")
                for c in candidates
                if c.case_id != resolved_id
            ],
            requires_human_review=False,
            resolved_by="deterministic_rule",
        )

    if not candidates:
        raise ValueError(
            "resolve() no debe invocarse sin candidatos: sin candidatos, esto no es "
            "un caso de resolución de expediente (docs/agent_contracts.md §4)"
        )

    if len(candidates) == 1:
        [only] = candidates
        return CaseResolved(
            resolution=only.case_id,
            confidence=0.90,
            evidence=[f"único candidato disponible: {', '.join(only.señales) or 'sin señales adicionales'}"],
            discarded_candidates=[],
            requires_human_review=False,
            resolved_by="deterministic_rule",
        )

    # Dos o más candidatos razonables sin evidencia determinista -> Claude decide,
    # con la regla crítica de "no adivinar" ya embebida en el prompt.
    if client is None:
        raise ValueError("hay múltiples candidatos ambiguos: se requiere un ClaudeClient (fake en pruebas)")

    raw = client.complete_json(
        prompt_version=PROMPT_VERSION,
        system_prompt=load_prompt(PROMPT_VERSION),
        input_payload={
            "mensaje_actual": {"subject": subject, "body": body_text, "remitente": from_, "fecha": date},
            "candidatos": [c.model_dump(by_alias=True) for c in candidates],
        },
        model=model,
    )
    return CaseResolved(
        resolution=raw["resolution"],
        confidence=raw["confidence"],
        evidence=raw["evidence"],
        discarded_candidates=[DiscardedCandidate(**d) for d in raw.get("discarded_candidates", [])],
        requires_human_review=raw["requires_human_review"],
        resolved_by="claude",
        prompt_version=PROMPT_VERSION,
    )
