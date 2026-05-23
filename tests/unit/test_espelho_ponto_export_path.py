from homologacao_ponto.models.espelho_ponto_export import (
    EspelhoPontoExport,
    RegistroDiaPonto,
    ServidorSelecionado,
)


def _make_export(nome="CELIO PROLICIANO MAIOLI", periodo="Dezembro/2025", run_id="abc123"):
    servidor = ServidorSelecionado(nome=nome)
    registro = RegistroDiaPonto(data="2025-12-15", marcacoes=["10:56"])
    return EspelhoPontoExport(
        run_id=run_id,
        captured_at="2026-05-23T00:00:00+00:00",
        servidor=servidor,
        registros=[registro],
        periodo_referencia=periodo,
    )


def test_output_subdir_uses_servidor_slug():
    export = _make_export()
    assert export.output_subdir == "servidores/celio-proliciano-maioli"


def test_output_filename_uses_periodo():
    export = _make_export()
    assert export.output_filename == "espelho-dezembro-2025.json"


def test_output_filename_fallback_when_no_periodo():
    export = _make_export(periodo=None, run_id="xyz999")
    assert export.output_filename == "espelho-xyz999.json"


def test_output_subdir_normalizes_accents():
    export = _make_export(nome="JOSÉ ARAÚJO")
    assert export.output_subdir == "servidores/jose-araujo"


def test_output_subdir_handles_special_chars():
    export = _make_export(nome="MARIA D'ALVA")
    assert "'" not in export.output_subdir
    assert export.output_subdir.startswith("servidores/maria")
