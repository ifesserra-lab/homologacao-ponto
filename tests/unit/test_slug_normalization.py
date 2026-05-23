from homologacao_ponto.models.espelho_ponto_export import _slug, _periodo_slug


def test_slug_basic_uppercase():
    assert _slug("CELIO PROLICIANO MAIOLI") == "celio-proliciano-maioli"


def test_slug_strips_accents():
    assert _slug("JOSÉ ARAÚJO") == "jose-araujo"
    assert _slug("MARIA CONCEIÇÃO") == "maria-conceicao"
    assert _slug("ANTÔNIO") == "antonio"


def test_slug_strips_cedilla():
    assert _slug("GONÇALVES") == "goncalves"


def test_slug_collapses_spaces():
    assert _slug("SILVA  SANTOS") == "silva-santos"


def test_slug_strips_apostrophe():
    result = _slug("MARIA D'ALVA")
    assert "'" not in result
    assert result == "maria-d-alva"


def test_slug_no_leading_trailing_hyphens():
    result = _slug("  NOME  ")
    assert not result.startswith("-")
    assert not result.endswith("-")


def test_periodo_slug_basic():
    assert _periodo_slug("Dezembro/2025", "fallback") == "dezembro-2025"


def test_periodo_slug_other_months():
    assert _periodo_slug("Maio/2026", "fallback") == "maio-2026"
    assert _periodo_slug("Janeiro/2024", "fallback") == "janeiro-2024"


def test_periodo_slug_fallback_when_none():
    assert _periodo_slug(None, "abc123") == "abc123"


def test_periodo_slug_fallback_when_empty():
    # empty string is falsy — use run_id
    assert _periodo_slug("", "xyz") == "xyz"
