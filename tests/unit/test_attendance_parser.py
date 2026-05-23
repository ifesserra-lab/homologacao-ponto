from homologacao_ponto.infrastructure.attendance_parser import AttendanceParser, SigrhPageSnapshot
from fixtures.sigrh_pages import ATTENDANCE_HTML


def test_attendance_parser_extracts_records() -> None:
    snapshot = SigrhPageSnapshot(
        url="https://sigrh.ifes.edu.br/sigrh/frequencia/espelho.jsf",
        title="Ponto",
        html=ATTENDANCE_HTML,
        captured_at="2026-05-20T12:00:00+00:00",
    )

    records = AttendanceParser().parse(snapshot)

    assert len(records) == 1
    assert records[0].point_date == "2026-05-20"
    assert records[0].entry_times == ["08:00", "13:00"]
    assert records[0].exit_times == ["12:00", "17:00"]


def test_attendance_parser_discards_malformed_rows() -> None:
    snapshot = SigrhPageSnapshot(
        url="https://sigrh.ifes.edu.br/sigrh/frequencia/espelho.jsf",
        title="Ponto",
        html="<tr class='registro-ponto'><td class='entrada'>08:00</td></tr>",
        captured_at="2026-05-20T12:00:00+00:00",
    )

    assert AttendanceParser().parse(snapshot) == []
