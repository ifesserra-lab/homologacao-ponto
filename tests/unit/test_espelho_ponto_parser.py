import pytest

from fixtures.sigrh_espelho_export_pages import (
    EMPTY_ESPELHO_PAGE_HTML,
    INVALID_PAGE_HTML,
    VALID_ESPELHO_PAGE_HTML,
    VALID_ESPELHO_WITH_RESUMO_HTML,
)
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


def test_parser_captures_resumo_all_16_fields() -> None:
    export = EspelhoPontoParser().parse(
        snapshot(VALID_ESPELHO_WITH_RESUMO_HTML),
        run_id="run-resumo",
        expected_server="Celio Proliciano Maioli",
        expected_identifier="1534589",
    )

    assert export.resumo is not None
    assert export.resumo.total_horas_homologadas == "49:25"
    assert export.resumo.carga_horaria_contratada == "160:00"
    assert export.resumo.carga_horaria_esperada_mes == "160:00"
    assert export.resumo.total_horas_registradas == "50:31"
    assert export.resumo.total_horas_justificadas == "00:00"
    assert export.resumo.saldo_mes_anterior_compensacao == "00:00"
    assert export.resumo.total_horas_mes_anterior_compensadas == "00:00"
    assert export.resumo.debito_mes_anterior_nao_compensado == "00:00"
    assert export.resumo.debito_mes_atual_nao_autorizado == "-61:25"
    assert export.resumo.outros_debitos_nao_compensados_vencidos == "00:00"
    assert export.resumo.totalizacao_debito_nao_compensavel == "-61:25"
    assert export.resumo.total_horas_pendentes_compensacao == "-09:10"
    assert export.resumo.saldo_horas_mes == "-09:10"
    assert export.resumo.saldo_horas_mes_compensar_proximo == "-09:10"
    assert export.resumo.credito_horas_disponivel_mes == "00:00"
    assert export.resumo.credito_em_horas == "00:00"


def test_parser_resumo_none_when_no_resumo_section() -> None:
    export = EspelhoPontoParser().parse(
        snapshot(VALID_ESPELHO_PAGE_HTML),
        run_id="run-no-resumo",
        expected_server="Celio Proliciano Maioli",
        expected_identifier="1534589",
    )

    assert export.resumo is None


def test_parser_preserves_negative_sign_in_resumo() -> None:
    export = EspelhoPontoParser().parse(
        snapshot(VALID_ESPELHO_WITH_RESUMO_HTML),
        run_id="run-neg",
        expected_server="Celio Proliciano Maioli",
        expected_identifier="1534589",
    )

    assert export.resumo is not None
    assert export.resumo.saldo_horas_mes == "-09:10"
    assert export.resumo.debito_mes_atual_nao_autorizado == "-61:25"


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
