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
