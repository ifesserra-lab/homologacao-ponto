import pytest

from homologacao_ponto.models import ServidorConsulta, ServidorResultado, normalize_server_name


def test_servidor_consulta_normalizes_name_and_identifier() -> None:
    consulta = ServidorConsulta("  Célio   Proliciano Maioli (1534589) ")

    assert consulta.normalized_name == "celio proliciano maioli 1534589"
    assert normalize_server_name("CÉLIO") == "celio"


def test_servidor_consulta_requires_name() -> None:
    with pytest.raises(ValueError):
        ServidorConsulta(" ")


def test_servidor_resultado_matches_name_and_identifier() -> None:
    consulta = ServidorConsulta("Celio Proliciano Maioli")
    result = ServidorResultado("CELIO PROLICIANO MAIOLI", "1534589", "1534589 CELIO PROLICIANO MAIOLI", True)

    assert result.matches(consulta)


def test_servidor_resultado_requires_selection_available_for_selectable_match() -> None:
    consulta = ServidorConsulta("Celio Proliciano Maioli")
    result = ServidorResultado("CELIO PROLICIANO MAIOLI", "1534589", "1534589 CELIO PROLICIANO MAIOLI", False)

    assert result.matches(consulta)
    assert not result.can_select
