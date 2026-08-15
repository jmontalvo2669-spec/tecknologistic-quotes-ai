"""Almacenamiento de adjuntos en memoria — sustituye a Cloud Storage
mientras no haya credenciales reales (GATE 1). 'No sobrescribir archivos
originales' (sección 9 de docs/architecture.md): put() es un no-op si la
ruta ya existe."""

from __future__ import annotations


class InMemoryBlobStore:
    def __init__(self) -> None:
        self._data: dict[str, bytes] = {}

    def put(self, storage_path: str, content: bytes) -> None:
        if storage_path in self._data:
            return
        self._data[storage_path] = content

    def get(self, storage_path: str) -> bytes | None:
        return self._data.get(storage_path)
