import pytest

from homologacao_ponto.models import EspelhoPontoExport, RegistroDiaPonto, ServidorSelecionado


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
