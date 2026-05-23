import pytest

from homologacao_ponto.models import EspelhoPontoExport, RegistroDiaPonto, ResumoHorasApuradas, ServidorSelecionado


def test_espelho_ponto_export_serializes_completed_report() -> None:
    servidor = ServidorSelecionado("CELIO PROLICIANO MAIOLI", "1534589")
    registro = RegistroDiaPonto(
        data="2026-05-02",
        dia_semana="Sabado",
        marcacoes=["07:58", "12:00"],
        ocorrencias=["Trabalho presencial"],
        observacoes=["Sem pendencias"],
        situacao="Homologado",
        textos_visiveis=["Credito 00:05"],
    )

    export = EspelhoPontoExport(
        run_id="run-123",
        captured_at="2026-05-20T12:00:00+00:00",
        servidor=servidor,
        periodo_referencia="Maio/2026",
        registros=[registro],
        mensagens=["Espelho gerado"],
    )

    data = export.to_dict()

    assert data["status"] == "completed"
    assert data["servidor"]["nome"] == "CELIO PROLICIANO MAIOLI"
    assert data["registros"][0]["marcacoes"] == ["07:58", "12:00"]
    assert "html" not in str(data).lower()


def test_espelho_ponto_export_empty_uses_empty_status() -> None:
    export = EspelhoPontoExport.empty(
        run_id="run-123",
        captured_at="2026-05-20T12:00:00+00:00",
        servidor=ServidorSelecionado("CELIO PROLICIANO MAIOLI"),
        periodo_referencia="Maio/2026",
        mensagens=["Sem registros"],
    )

    assert export.status == "empty"
    assert export.registros == []


def test_registro_dia_ponto_requires_visible_data() -> None:
    with pytest.raises(ValueError):
        RegistroDiaPonto(data="")


def _make_registro() -> RegistroDiaPonto:
    return RegistroDiaPonto(
        data="2026-05-02",
        marcacoes=["07:58", "17:00"],
    )


def test_export_to_dict_has_resumo_and_schema_version_2_when_resumo_set() -> None:
    resumo = ResumoHorasApuradas(total_horas_homologadas="49:25", saldo_horas_mes="-09:10")
    export = EspelhoPontoExport(
        run_id="run-1",
        captured_at="2026-05-20T12:00:00+00:00",
        servidor=ServidorSelecionado("CELIO PROLICIANO MAIOLI", "1534589"),
        registros=[_make_registro()],
        resumo=resumo,
    )

    data = export.to_dict()

    assert data["schema_version"] == 2
    assert data["resumo"] is not None
    assert data["resumo"]["total_horas_homologadas"] == "49:25"
    assert data["resumo"]["saldo_horas_mes"] == "-09:10"


def test_export_to_dict_has_resumo_null_and_schema_version_2_when_resumo_none() -> None:
    export = EspelhoPontoExport(
        run_id="run-1",
        captured_at="2026-05-20T12:00:00+00:00",
        servidor=ServidorSelecionado("CELIO PROLICIANO MAIOLI", "1534589"),
        registros=[_make_registro()],
    )

    data = export.to_dict()

    assert data["schema_version"] == 2
    assert "resumo" in data
    assert data["resumo"] is None


def test_export_empty_has_resumo_null() -> None:
    export = EspelhoPontoExport.empty(
        run_id="run-1",
        captured_at="2026-05-20T12:00:00+00:00",
        servidor=ServidorSelecionado("CELIO PROLICIANO MAIOLI"),
        periodo_referencia="Maio/2026",
    )

    data = export.to_dict()

    assert data["schema_version"] == 2
    assert data["resumo"] is None
