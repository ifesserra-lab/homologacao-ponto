import pytest

from homologacao_ponto.models import AttendanceRecord


def test_attendance_record_requires_minimum_fields() -> None:
    with pytest.raises(ValueError):
        AttendanceRecord("", [], [], "https://sigrh.ifes.edu.br/sigrh/frequencia", "now")
    with pytest.raises(ValueError):
        AttendanceRecord("2026-05-20", [], [], "", "now")
    with pytest.raises(ValueError):
        AttendanceRecord("2026-05-20", [], [], "https://sigrh.ifes.edu.br/sigrh/frequencia", "")


def test_attendance_record_serializes_expected_fields() -> None:
    record = AttendanceRecord(
        point_date="2026-05-20",
        entry_times=["08:00"],
        exit_times=["17:00"],
        source_url="https://sigrh.ifes.edu.br/sigrh/frequencia",
        collected_at="2026-05-20T12:00:00+00:00",
    )

    assert record.to_dict()["entry_times"] == ["08:00"]

