import pytest

from homologacao_ponto.models import AttendanceRecord, CrawlResult, CrawlStatus


def test_completed_empty_result_requires_message() -> None:
    with pytest.raises(ValueError):
        CrawlResult(username_ref="paulo", visited_page_count=1)

    result = CrawlResult(
        username_ref="paulo",
        visited_page_count=1,
        message="nenhum registro encontrado",
    )

    assert result.record_count == 0
    assert result.to_dict()["status"] == "completed"


def test_partial_and_blocked_require_message() -> None:
    with pytest.raises(ValueError):
        CrawlResult(username_ref="paulo", visited_page_count=1, status=CrawlStatus.PARTIAL)
    with pytest.raises(ValueError):
        CrawlResult(username_ref="paulo", visited_page_count=1, status=CrawlStatus.BLOCKED)


def test_result_counts_records_and_caps_pages() -> None:
    record = AttendanceRecord(
        "2026-05-20",
        ["08:00"],
        ["17:00"],
        "https://sigrh.ifes.edu.br/sigrh/frequencia",
        "2026-05-20T12:00:00+00:00",
    )

    result = CrawlResult(username_ref="paulo", visited_page_count=20, records=[record])

    assert result.record_count == 1
    with pytest.raises(ValueError):
        CrawlResult(username_ref="paulo", visited_page_count=21, records=[record])

