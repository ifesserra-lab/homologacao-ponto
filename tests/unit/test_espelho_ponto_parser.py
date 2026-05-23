import pytest

from fixtures.sigrh_espelho_export_pages import EMPTY_ESPELHO_PAGE_HTML, INVALID_PAGE_HTML, VALID_ESPELHO_PAGE_HTML
from homologacao_ponto.infrastructure.attendance_parser import SigrhPageSnapshot
from homologacao_ponto.infrastructure.espelho_ponto_parser import EspelhoPontoParseError, EspelhoPontoParser


def snapshot(html: str) -> SigrhPageSnapshot:
    return SigrhPageSnapshot(
        "https://sigrh.ifes.edu.br/sigrh/frequencia/espelho.jsf",
        "Espelho de Ponto",
        html,
        "2026-05-20T12:00:00+00:00",
    )


def test_parser_extracts_valid_daily_records() -> None:
    export = EspelhoPontoParser().parse(
        snapshot(VALID_ESPELHO_PAGE_HTML),
        run_id="run-123",
        expected_server="Celio Proliciano Maioli",
        expected_identifier="1534589",
    )

    assert export.status == "completed"
    assert export.servidor.nome == "CELIO PROLICIANO MAIOLI"
    assert export.periodo_referencia == "Maio/2026"
    assert export.registros[0].data == "2026-05-02"
    assert export.registros[0].marcacoes == ["07:58", "12:00", "13:00", "17:03"]


def test_parser_marks_empty_espelho_as_empty() -> None:
    export = EspelhoPontoParser().parse(
        snapshot(EMPTY_ESPELHO_PAGE_HTML),
        run_id="run-123",
        expected_server="Celio Proliciano Maioli",
        expected_identifier="1534589",
    )

    assert export.status == "empty"
    assert export.registros == []
    assert export.mensagens == ["Sem registros de ponto para o periodo"]


def test_parser_rejects_invalid_page() -> None:
    with pytest.raises(EspelhoPontoParseError):
        EspelhoPontoParser().parse(snapshot(INVALID_PAGE_HTML), run_id="run-123", expected_server="Celio Proliciano Maioli")


def test_parser_server_name_not_repeated_when_name_in_multiple_nodes() -> None:
    # Regression: visible_text join caused regex to capture name N times concatenated
    html = """<html><head><title>Espelho de Ponto</title></head><body>
    <h1>Espelho de Ponto</h1>
    <span>Servidor: </span><span>CELIO PROLICIANO MAIOLI</span>
    <span>Servidor: </span><span>CELIO PROLICIANO MAIOLI</span>
    <span>Servidor: </span><span>CELIO PROLICIANO MAIOLI</span>
    <p>Nenhum registro de ponto de servidor(es) segundo os criterios de busca.</p>
    </body></html>"""
    export = EspelhoPontoParser().parse(
        snapshot(html),
        run_id="run-reg",
        expected_server="Celio Proliciano Maioli",
    )
    assert export.servidor.nome == "CELIO PROLICIANO MAIOLI"


def test_parser_server_name_not_repeated_when_jsf_concatenates_in_one_node() -> None:
    # Regression: JSF renders adjacent output components without whitespace,
    # producing one text node like "Servidor: NAMENAME NAME" (no spaces between reps).
    # Expected: captured group starts with expected name → return expected only.
    concatenated = "CELIO PROLICIANO MAIOLICELIOPROLICIANOMAIOLICELIOPROLICIANOMAIOLI"
    html = f"""<html><head><title>Espelho de Ponto</title></head><body>
    <h1>Espelho de Ponto</h1>
    <div>Servidor: {concatenated}</div>
    <p>Nenhum registro de ponto de servidor(es) segundo os criterios de busca.</p>
    </body></html>"""
    export = EspelhoPontoParser().parse(
        snapshot(html),
        run_id="run-reg2",
        expected_server="Celio Proliciano Maioli",
    )
    assert export.servidor.nome == "CELIO PROLICIANO MAIOLI"
