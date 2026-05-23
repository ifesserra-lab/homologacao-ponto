"""Tests for AdmissaoDetector — probe-based historical period detection."""

import datetime
import pytest

from homologacao_ponto.infrastructure.admissao_detector import (
    AdmissaoDetector,
    AdmissaoNaoDetectadaError,
)
from homologacao_ponto.models.batch_config import BatchEntry

ENTRY = BatchEntry(nome="CELIO", siape="123")
TODAY = datetime.date(2026, 5, 23)


class FakeApp:
    """Fake app with configurable success/failure by (mes, ano)."""

    def __init__(self, success_periods: set[tuple[int, int]]) -> None:
        self._success = success_periods
        self.calls: list[tuple] = []

    def _run_single_espelho(self, session, servidor, siape, mes, ano):
        self.calls.append((mes, ano))
        from homologacao_ponto.app import AppResult

        if (mes, ano) in self._success:
            return AppResult(0, "ok", None)
        return AppResult(4, "falhou", None)


def test_detect_returns_recent_success_periods():
    # last 3 months succeed, everything before fails
    success = {(5, 2026), (4, 2026), (3, 2026)}
    app = FakeApp(success)
    detector = AdmissaoDetector()
    periodos = detector.detect(app, None, ENTRY, TODAY)
    assert (3, 2026) in periodos
    assert (4, 2026) in periodos
    assert (5, 2026) in periodos


def test_detect_stops_after_3_consecutive_failures():
    # only mar-may 2026 succeed
    success = {(5, 2026), (4, 2026), (3, 2026)}
    app = FakeApp(success)
    detector = AdmissaoDetector()
    detector.detect(app, None, ENTRY, TODAY)
    # must stop probing after 3 consecutive failures (feb, jan, dec/2025)
    total_calls = len(app.calls)
    # should not probe all the way back to year 2000
    assert total_calls < 20


def test_detect_returns_periods_in_chronological_order():
    success = {(5, 2026), (4, 2026), (3, 2026)}
    app = FakeApp(success)
    periodos = AdmissaoDetector().detect(app, None, ENTRY, TODAY)
    assert periodos == sorted(periodos, key=lambda p: (p[1], p[0]))


def test_detect_raises_when_no_period_found():
    app = FakeApp(success_periods=set())
    with pytest.raises(AdmissaoNaoDetectadaError):
        AdmissaoDetector().detect(app, None, ENTRY, TODAY)


def test_detect_respects_max_years_limit():
    # all periods succeed — but probe must stop at MAX_ANOS_RETROATIVOS
    all_success = {(m, a) for a in range(1990, 2027) for m in range(1, 13)}
    app = FakeApp(success_periods=all_success)
    today = datetime.date(2026, 5, 23)
    periodos = AdmissaoDetector().detect(app, None, ENTRY, today)
    oldest_ano = min(a for _, a in periodos)
    assert oldest_ano >= today.year - AdmissaoDetector.MAX_ANOS_RETROATIVOS
