import datetime

from homologacao_ponto.models.batch_config import BatchConfig, BatchEntry
from homologacao_ponto.services.periodo_expander import PeriodoExpander

ENTRY = BatchEntry(nome="CELIO", siape="123")
TODAY = datetime.date(2026, 5, 23)


def _config(anos=None, mes=None, ano=None) -> BatchConfig:
    return BatchConfig(servidores=[ENTRY], anos=anos, mes=mes, ano=ano)


def test_expand_anos_list_single_year_returns_12():
    periodos = PeriodoExpander.expand(_config(anos=[2025]), ENTRY, TODAY)
    assert len(periodos) == 12
    assert periodos[0] == (1, 2025)
    assert periodos[-1] == (12, 2025)


def test_expand_anos_list_two_years_excludes_future():
    # 2025: 12 meses; 2026: jan-mai = 5 meses
    periodos = PeriodoExpander.expand(_config(anos=[2025, 2026]), ENTRY, TODAY)
    assert len(periodos) == 17
    assert (12, 2025) in periodos
    assert (5, 2026) in periodos
    assert (6, 2026) not in periodos


def test_expand_anos_list_sorted_chronological():
    periodos = PeriodoExpander.expand(_config(anos=[2026, 2025]), ENTRY, TODAY)
    anos_sorted = [a for _, a in periodos]
    assert anos_sorted == sorted(anos_sorted)


def test_expand_anos_duplicates_deduplicated():
    periodos_dup = PeriodoExpander.expand(_config(anos=[2025, 2025]), ENTRY, TODAY)
    periodos_single = PeriodoExpander.expand(_config(anos=[2025]), ENTRY, TODAY)
    assert periodos_dup == periodos_single


def test_expand_anos_none_returns_single_period_from_entry():
    entry_override = BatchEntry(nome="CELIO", siape="123", mes=3, ano=2024)
    periodos = PeriodoExpander.expand(_config(), entry_override, TODAY)
    assert periodos == [(3, 2024)]


def test_expand_anos_none_falls_back_to_config():
    periodos = PeriodoExpander.expand(_config(mes=7, ano=2023), ENTRY, TODAY)
    assert periodos == [(7, 2023)]


def test_expand_anos_none_falls_back_to_today():
    periodos = PeriodoExpander.expand(_config(), ENTRY, TODAY)
    assert periodos == [(TODAY.month, TODAY.year)]


def test_expand_anos_all_returns_empty_list():
    # "All" signals BatchService to use AdmissaoDetector
    periodos = PeriodoExpander.expand(_config(anos="All"), ENTRY, TODAY)
    assert periodos == []


def test_expand_years_only_up_to_current_month_in_current_year():
    today = datetime.date(2026, 3, 15)
    periodos = PeriodoExpander.expand(_config(anos=[2026]), ENTRY, today)
    assert len(periodos) == 3  # jan, fev, mar
    assert (3, 2026) in periodos
    assert (4, 2026) not in periodos
