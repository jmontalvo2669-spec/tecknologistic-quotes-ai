from pathlib import Path

from services.extractor.service import extract
from services.shared.claude_client import FakeClaudeClient
from services.shared.settings import Settings

FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_caso_1_rfq_excel_1_linea():
    content = (FIXTURES / "rfq_simple_1_linea.xlsx").read_bytes()

    result = extract(document_type="excel", content=content)

    assert len(result.lines) == 1
    assert result.line_count_confidence >= 0.90
    assert result.requires_human_review is False
    assert result.lines[0].quantity == 12
    assert result.lines[0].standard == "API 6D"


def test_caso_2_rfq_excel_500_lineas_sin_timeout_ni_truncar():
    content = (FIXTURES / "rfq_masiva_500_lineas.xlsx").read_bytes()

    result = extract(document_type="excel", content=content)

    assert len(result.lines) == 500
    assert result.requires_human_review is False


def test_caso_3_cantidades_identicas_se_fusionan_en_una_linea():
    content = (FIXTURES / "rfq_lineas_duplicadas.xlsx").read_bytes()

    result = extract(document_type="excel", content=content)

    assert len(result.lines) == 1
    assert result.lines[0].quantity == 100  # 40 + 35 + 25


def test_caso_11_excel_multitab_ignora_hojas_de_notas():
    content = (FIXTURES / "rfq_multitab.xlsx").read_bytes()

    result = extract(document_type="excel", content=content)

    assert len(result.lines) == 2
    descripciones = {line.description for line in result.lines}
    assert descripciones == {'Brida 6" 150#', "Codo 90° 4\""}


def test_caso_9_pdf_ilegible_no_inventa_lineas():
    def handler(prompt_version, payload, model):
        return {
            "lines": [],
            "line_count_confidence": 0.0,
            "ambiguous_groupings": ["OCR devolvió texto sin sentido"],
            "requires_human_review": True,
        }

    client = FakeClaudeClient(handler)

    result = extract(
        document_type="pdf_escaneado",
        raw_content="asd9812 %%% ilegible",
        context=None,
        client=client,
    )

    assert result.lines == []
    assert result.requires_human_review is True


def test_caso_10_imagen_ejemplo_de_extractor_v1():
    """Ejemplo de prompts/extractor_v1.txt."""

    def handler(prompt_version, payload, model):
        return {
            "lines": [
                {
                    "line_id": "1",
                    "description": "tornillos M10 acero inoxidable",
                    "quantity": 100,
                    "unit": "pza",
                    "manufacturer": None,
                    "part_number": None,
                    "standard": None,
                    "specification": "acero inoxidable",
                    "observations": None,
                },
                {
                    "line_id": "2",
                    "description": 'bridas 6 pulgadas 150#',
                    "quantity": 3,
                    "unit": "pza",
                    "manufacturer": None,
                    "part_number": None,
                    "standard": "ASTM A105",
                    "specification": '6", clase 150#',
                    "observations": "sin marca especificada",
                },
            ],
            "line_count_confidence": 0.92,
            "ambiguous_groupings": [],
            "requires_human_review": False,
        }

    client = FakeClaudeClient(handler)
    result = extract(
        document_type="imagen",
        raw_content='100 tornillos M10 acero inox / 3 bridas 6" 150# ASTM A105 (sin marca)',
        context=None,
        client=client,
        config=Settings(claude_model_reasoning="reasoning-model"),
    )

    assert len(result.lines) == 2
    assert result.requires_human_review is False


def test_confianza_baja_fuerza_revision_humana_sin_importar_la_fuente():
    def handler(prompt_version, payload, model):
        return {
            "lines": [{"line_id": "1", "description": "algo dudoso", "quantity": None,
                        "unit": None, "manufacturer": None, "part_number": None,
                        "standard": None, "specification": None, "observations": None}],
            "line_count_confidence": 0.5,
            "ambiguous_groupings": ["agrupación dudosa"],
            "requires_human_review": False,  # el prompt no lo marcó, el umbral del sistema debe forzarlo
        }

    client = FakeClaudeClient(handler)
    result = extract(document_type="imagen", raw_content="texto", context=None, client=client)

    assert result.requires_human_review is True
