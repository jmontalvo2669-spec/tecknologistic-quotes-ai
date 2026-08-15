from services.traceability.service import compute_completeness, p0_checks


def test_expediente_completo_score_1():
    checks = p0_checks(
        correo_ingerido=True, lineas_extraidas=True, expediente_resuelto=True, cotizador_asignado=True
    )
    result = compute_completeness("TQL-2026-000001", checks)

    assert result.completeness_score == 1.0
    assert result.gaps == []


def test_expediente_incompleto_reporta_gaps():
    checks = p0_checks(
        correo_ingerido=True, lineas_extraidas=True, expediente_resuelto=False, cotizador_asignado=False
    )
    result = compute_completeness("TQL-2026-000001", checks)

    assert result.completeness_score == 0.5
    assert set(result.gaps) == {"expediente_resuelto", "cotizador_asignado"}


def test_sin_checks_score_cero():
    result = compute_completeness("TQL-2026-000001", {})
    assert result.completeness_score == 0.0
    assert result.gaps
