"""Verifica que las migraciones de Alembic crean el esquema esperado.

Corre contra SQLite (nunca contra un Postgres real) — ver migrations/env.py.
"""

import subprocess
import sys
from pathlib import Path

import sqlalchemy as sa

REPO_ROOT = Path(__file__).resolve().parents[2]


def test_alembic_upgrade_head_creates_expected_tables(tmp_path):
    db_path = tmp_path / "test_migrations.db"
    database_url = f"sqlite:///{db_path}"

    result = subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=REPO_ROOT,
        env={"DATABASE_URL": database_url, "PATH": "/usr/bin:/bin"},
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr

    engine = sa.create_engine(database_url)
    inspector = sa.inspect(engine)
    tables = set(inspector.get_table_names())

    assert {"expedientes", "ingested_messages", "state_transitions"} <= tables
