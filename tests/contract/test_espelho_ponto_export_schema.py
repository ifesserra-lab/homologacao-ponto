from jsonschema import validate

from fixtures.espelho_export_samples import load_contract_schema, sample_export_dict


def test_espelho_ponto_export_schema_accepts_valid_sample() -> None:
    validate(sample_export_dict(), load_contract_schema("espelho-ponto-export.schema.json"))


def test_espelho_ponto_export_schema_rejects_raw_html_field() -> None:
    sample = sample_export_dict()
    sample["raw_html"] = "<html></html>"

    try:
        validate(sample, load_contract_schema("espelho-ponto-export.schema.json"))
    except Exception as exc:
        assert "Additional properties" in str(exc)
    else:
        raise AssertionError("schema accepted raw_html")


def test_registro_contains_new_calculated_fields():
    from homologacao_ponto.models.espelho_ponto_export import RegistroDiaPonto, ServidorSelecionado, EspelhoPontoExport
    servidor = ServidorSelecionado(nome="TESTE")
    registro = RegistroDiaPonto(
        data="2025-12-15",
        hr="07:00",
        hc="01:05",
        he=None,
        ha=None,
        hh=None,
        credito="01:05",
        debito=None,
        saldo_no_mes="-06:55",
        credito_acumulado="00:00",
        dnc=None,
    )
    export = EspelhoPontoExport(
        run_id="schema-test",
        captured_at="2026-05-23T00:00:00+00:00",
        servidor=servidor,
        registros=[registro],
    )
    data = export.to_dict()
    reg = data["registros"][0]
    for key in ("hr", "hc", "he", "ha", "hh", "credito", "debito", "saldo_no_mes", "credito_acumulado", "dnc"):
        assert key in reg, f"key {key!r} missing from registros[0]"
    assert reg["hr"] == "07:00"
    assert reg["he"] is None
    assert reg["saldo_no_mes"] == "-06:55"
