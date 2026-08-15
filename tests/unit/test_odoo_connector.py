import pytest

from odoo.fake_client import FakeOdooClient
from services.odoo_connector.service import OdooModelNotValidated, write_record
from services.shared.repositories import InMemoryOdooIdempotencyStore


def test_primera_escritura_crea_y_verifica():
    client = FakeOdooClient()
    store = InMemoryOdooIdempotencyStore()

    result = write_record(
        case_id="TQL-2026-000001",
        odoo_model="sale.order",
        values={"name": "SO-TEST"},
        idempotency_key="key-1",
        client=client,
        idempotency_store=store,
    )

    assert result.operation == "create"
    assert result.verified is True
    assert result.error is None


def test_misma_idempotency_key_actualiza_en_vez_de_duplicar():
    client = FakeOdooClient()
    store = InMemoryOdooIdempotencyStore()

    primero = write_record(
        case_id="TQL-2026-000001", odoo_model="sale.order", values={"name": "SO-TEST"},
        idempotency_key="key-1", client=client, idempotency_store=store,
    )
    segundo = write_record(
        case_id="TQL-2026-000001", odoo_model="sale.order", values={"name": "SO-TEST-v2"},
        idempotency_key="key-1", client=client, idempotency_store=store,
    )

    assert segundo.operation == "update"
    assert segundo.odoo_id == primero.odoo_id  # mismo registro, no un duplicado


def test_modelo_no_validado_se_rechaza_antes_de_escribir():
    client = FakeOdooClient()
    store = InMemoryOdooIdempotencyStore()

    with pytest.raises(OdooModelNotValidated):
        write_record(
            case_id="TQL-2026-000001", odoo_model="modelo.inventado", values={},
            idempotency_key="key-1", client=client, idempotency_store=store,
        )


def test_caso_18_fallo_despues_de_escritura_no_asume_exito_silencioso():
    store = InMemoryOdooIdempotencyStore()
    client = FakeOdooClient()

    # Forzamos que el VERIFY falle para el próximo id que se cree (id=1).
    client._fail_verify_for.add(1)

    result = write_record(
        case_id="TQL-2026-000001", odoo_model="sale.order", values={"name": "SO-TEST"},
        idempotency_key="key-1", client=client, idempotency_store=store,
    )

    assert result.verified is False
    assert result.error is not None
    assert "no verificada" in result.error
