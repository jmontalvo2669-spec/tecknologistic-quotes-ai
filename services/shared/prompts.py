"""Carga los prompts versionados de prompts/ (sección 29 de
docs/architecture.md) tal como están en el repo, sin reescribir su lógica
en código (regla de contrato de docs/agent_contracts.md)."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parents[2] / "prompts"


@lru_cache
def load_prompt(name: str) -> str:
    path = PROMPTS_DIR / f"{name}.txt"
    return path.read_text(encoding="utf-8")
