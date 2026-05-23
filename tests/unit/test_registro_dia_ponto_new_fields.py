from homologacao_ponto.models.espelho_ponto_export import RegistroDiaPonto


def test_registro_accepts_all_new_fields():
    r = RegistroDiaPonto(
        data="2025-12-15",
        dia_semana="Segunda",
        marcacoes=["10:56", "19:01"],
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
    assert r.hr == "07:00"
    assert r.hc == "01:05"
    assert r.he is None
    assert r.saldo_no_mes == "-06:55"
    assert r.credito_acumulado == "00:00"
    assert r.dnc is None


def test_to_dict_includes_all_new_fields():
    r = RegistroDiaPonto(
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
    d = r.to_dict()
    for key in ("hr", "hc", "he", "ha", "hh", "credito", "debito", "saldo_no_mes", "credito_acumulado", "dnc"):
        assert key in d, f"key {key!r} missing from to_dict()"


def test_to_dict_null_fields_not_omitted():
    r = RegistroDiaPonto(data="2025-12-15", marcacoes=["08:00"])
    d = r.to_dict()
    # All 10 new fields must appear as None/null, never omitted
    for key in ("hr", "hc", "he", "ha", "hh", "credito", "debito", "saldo_no_mes", "credito_acumulado", "dnc"):
        assert key in d
        assert d[key] is None


def test_existing_fields_still_present():
    r = RegistroDiaPonto(data="2025-12-15", marcacoes=["08:00"])
    d = r.to_dict()
    for key in ("data", "dia_semana", "marcacoes", "ocorrencias", "observacoes", "situacao", "textos_visiveis"):
        assert key in d
