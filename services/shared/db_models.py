"""Modelos SQLAlchemy — tabla a tabla, sección 7 de docs/architecture.md
(modelo de expediente) y sección 19 (idempotencia).

No se usan todavía desde los servicios de PASO 6: los servicios operan con
repositorios en memoria (ver services/shared/repositories.py) mientras no
haya un Postgres real conectado. Este módulo existe para que las
migraciones de Alembic (migrations/) tengan un esquema real que crear y
verificar contra SQLite en pruebas.
"""

from __future__ import annotations

import datetime as dt

from sqlalchemy import DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class IngestedMessage(Base):
    """Idempotencia de Gmail Ingest (docs/agent_contracts.md §1)."""

    __tablename__ = "ingested_messages"

    message_hash: Mapped[str] = mapped_column(String, primary_key=True)
    gmail_message_id: Mapped[str] = mapped_column(String, nullable=False)
    gmail_thread_id: Mapped[str] = mapped_column(String, nullable=False)
    case_id: Mapped[str | None] = mapped_column(
        String, ForeignKey("expedientes.case_id"), nullable=True
    )
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False)


class Expediente(Base):
    """Expediente TQL — sección 7 de docs/architecture.md."""

    __tablename__ = "expedientes"

    case_id: Mapped[str] = mapped_column(String, primary_key=True)
    estado_actual: Mapped[str] = mapped_column(String, nullable=False)
    gmail_thread_id: Mapped[str] = mapped_column(String, nullable=False)
    cotizador_asignado: Mapped[str | None] = mapped_column(String, nullable=True)
    carga_antes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    carga_despues: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False)


class StateTransition(Base):
    """Auditoría de transiciones — regla general #3 de docs/state_machine.md."""

    __tablename__ = "state_transitions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    case_id: Mapped[str] = mapped_column(
        String, ForeignKey("expedientes.case_id"), nullable=False
    )
    estado_origen: Mapped[str | None] = mapped_column(String, nullable=True)
    estado_destino: Mapped[str] = mapped_column(String, nullable=False)
    evento: Mapped[str] = mapped_column(String, nullable=False)
    agente_actor: Mapped[str] = mapped_column(String, nullable=False)
    timestamp: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False)
    motivo: Mapped[str] = mapped_column(String, nullable=False)
    correlation_id: Mapped[str] = mapped_column(String, nullable=False)
