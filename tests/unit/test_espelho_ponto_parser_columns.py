from homologacao_ponto.infrastructure.espelho_ponto_parser import EspelhoPontoParser
from homologacao_ponto.infrastructure.attendance_parser import SigrhPageSnapshot
from tests.fixtures.sigrh_espelho_export_pages import (
    SIGRH_FULL_TABLE_ESPELHO_HTML,
    SIGRH_SPARSE_TABLE_ESPELHO_HTML,
)


def _snapshot(html: str) -> SigrhPageSnapshot:
    return SigrhPageSnapshot(url="http://sigrh/espelho", title="Espelho de Ponto", html=html, captured_at="2026-05-23T00:00:00+00:00")


def _parse(html: str):
    parser = EspelhoPontoParser()
    return parser.parse(_snapshot(html), run_id="test123", expected_server="CELIO PROLICIANO MAIOLI")


def test_parser_extracts_hr_field():
    export = _parse(SIGRH_FULL_TABLE_ESPELHO_HTML)
    row = next(r for r in export.registros if r.data == "2025-12-15")
    assert row.hr == "07:00", f"expected '07:00', got {row.hr!r}"


def test_parser_extracts_hc_field():
    export = _parse(SIGRH_FULL_TABLE_ESPELHO_HTML)
    row = next(r for r in export.registros if r.data == "2025-12-15")
    assert row.hc == "01:05", f"expected '01:05', got {row.hc!r}"


def test_parser_maps_dashes_to_none():
    export = _parse(SIGRH_FULL_TABLE_ESPELHO_HTML)
    row = next(r for r in export.registros if r.data == "2025-12-15")
    assert row.he is None
    assert row.ha is None
    assert row.dnc is None


def test_parser_extracts_saldo_no_mes():
    export = _parse(SIGRH_FULL_TABLE_ESPELHO_HTML)
    row = next(r for r in export.registros if r.data == "2025-12-15")
    assert row.saldo_no_mes == "-06:55"


def test_parser_extracts_credito_acumulado():
    export = _parse(SIGRH_FULL_TABLE_ESPELHO_HTML)
    row = next(r for r in export.registros if r.data == "2025-12-15")
    assert row.credito_acumulado == "00:00"


def test_parser_sparse_row_fields_are_none():
    """Row with only 2 cells (no calculated columns) — all new fields must be None."""
    export = _parse(SIGRH_SPARSE_TABLE_ESPELHO_HTML)
    assert len(export.registros) >= 1
    row = export.registros[0]
    for attr in ("hr", "hc", "he", "ha", "hh", "credito", "debito", "saldo_no_mes", "credito_acumulado", "dnc"):
        assert getattr(row, attr) is None, f"{attr} should be None for sparse row"


def test_parser_negative_saldo_preserved():
    export = _parse(SIGRH_FULL_TABLE_ESPELHO_HTML)
    row = next(r for r in export.registros if r.data == "2025-12-20")
    assert row.debito == "-08:00"
    assert row.saldo_no_mes == "-08:00"


def test_parser_row_with_only_2_cells_new_fields_are_none():
    """Row with only 2 cells (date + times, no calculated columns) — all 10 new fields must be None."""
    from tests.fixtures.sigrh_espelho_export_pages import SIGRH_SPARSE_TABLE_ESPELHO_HTML
    export = _parse(SIGRH_SPARSE_TABLE_ESPELHO_HTML)
    assert len(export.registros) >= 1
    row = export.registros[0]
    for attr in ("hr", "hc", "he", "ha", "hh", "credito", "debito", "saldo_no_mes", "credito_acumulado", "dnc"):
        val = getattr(row, attr)
        assert val is None, f"{attr} should be None for sparse row, got {val!r}"


def test_parser_all_dashes_map_to_none():
    """Row where every calculated cell contains '---' — all 10 new fields must be None."""
    from tests.fixtures.sigrh_espelho_export_pages import SIGRH_FULL_TABLE_ESPELHO_HTML
    export = _parse(SIGRH_FULL_TABLE_ESPELHO_HTML)
    # Row 2 (index 1, date 16/12/2025) has all '---' in calculated columns
    row = next(r for r in export.registros if r.data == "2025-12-16")
    for attr in ("hr", "hc", "he", "ha", "hh", "credito", "debito", "saldo_no_mes", "credito_acumulado", "dnc"):
        val = getattr(row, attr)
        assert val is None, f"{attr} should be None when cell is '---', got {val!r}"


def test_parser_negative_value_preserved_as_string():
    """-08:00 in debito cell must survive as-is, not be converted or nulled."""
    from tests.fixtures.sigrh_espelho_export_pages import SIGRH_FULL_TABLE_ESPELHO_HTML
    export = _parse(SIGRH_FULL_TABLE_ESPELHO_HTML)
    row = next(r for r in export.registros if r.data == "2025-12-20")
    assert row.debito == "-08:00"
    assert row.saldo_no_mes == "-08:00"
