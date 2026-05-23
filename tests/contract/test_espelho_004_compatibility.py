from homologacao_ponto.models.espelho_ponto_export import (
    EspelhoPontoExport,
    RegistroDiaPonto,
    ServidorSelecionado,
)

SPEC_004_REGISTRO_KEYS = {
    "data", "dia_semana", "marcacoes", "ocorrencias",
    "observacoes", "situacao", "textos_visiveis",
}

SPEC_004_EXPORT_KEYS = {
    "schema_version", "run_id", "captured_at", "status",
    "servidor", "periodo_referencia", "mensagens", "registros", "fonte",
}

NEW_FIELDS = {
    "hr", "hc", "he", "ha", "hh",
    "credito", "debito", "saldo_no_mes", "credito_acumulado", "dnc",
}


def test_all_spec_004_registro_keys_present():
    r = RegistroDiaPonto(data="2025-12-15", marcacoes=["10:00"])
    d = r.to_dict()
    for key in SPEC_004_REGISTRO_KEYS:
        assert key in d, f"spec-004 key '{key}' missing from RegistroDiaPonto.to_dict()"


def test_all_spec_004_export_keys_present():
    servidor = ServidorSelecionado(nome="TESTE")
    registro = RegistroDiaPonto(data="2025-12-15", marcacoes=["10:00"])
    export = EspelhoPontoExport(
        run_id="compat-test",
        captured_at="2026-05-23T00:00:00+00:00",
        servidor=servidor,
        registros=[registro],
    )
    d = export.to_dict()
    for key in SPEC_004_EXPORT_KEYS:
        assert key in d, f"spec-004 key '{key}' missing from EspelhoPontoExport.to_dict()"


def test_new_fields_additive_not_replacing():
    r = RegistroDiaPonto(data="2025-12-15", marcacoes=["10:00"])
    d = r.to_dict()
    assert SPEC_004_REGISTRO_KEYS.issubset(d.keys()), "spec-004 fields must be present"
    assert NEW_FIELDS.issubset(d.keys()), "new fields must also be present"


def test_schema_version_unchanged():
    servidor = ServidorSelecionado(nome="TESTE")
    registro = RegistroDiaPonto(data="2025-12-15", marcacoes=["10:00"])
    export = EspelhoPontoExport(
        run_id="compat-test",
        captured_at="2026-05-23T00:00:00+00:00",
        servidor=servidor,
        registros=[registro],
    )
    assert export.to_dict()["schema_version"] == 1
