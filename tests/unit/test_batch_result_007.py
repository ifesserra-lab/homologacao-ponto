from homologacao_ponto.models.batch_result import BatchEntryResult


def test_entry_result_with_mes_ano():
    entry = BatchEntryResult(
        nome="CELIO", siape="123", status="completed", mes=5, ano=2025
    )
    assert entry.mes == 5
    assert entry.ano == 2025


def test_entry_result_to_dict_includes_mes_ano():
    entry = BatchEntryResult(
        nome="CELIO", siape="123", status="completed", mes=5, ano=2025
    )
    d = entry.to_dict()
    assert d["mes"] == 5
    assert d["ano"] == 2025


def test_entry_result_to_dict_omits_mes_ano_when_none():
    entry = BatchEntryResult(nome="CELIO", siape="123", status="completed")
    d = entry.to_dict()
    assert "mes" not in d
    assert "ano" not in d


def test_entry_result_defaults_mes_ano_none():
    entry = BatchEntryResult(nome="CELIO", siape="123", status="failed")
    assert entry.mes is None
    assert entry.ano is None
