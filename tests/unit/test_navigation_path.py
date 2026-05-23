from homologacao_ponto.models import NavigationPath


def test_navigation_path_has_canonical_labels_and_step_wait() -> None:
    path = NavigationPath.default()

    assert path.labels == [
        "Chefia de Unidade",
        "Homologacao de Ponto Eletronico",
        "Relatorio",
        "Espelho do Ponto",
    ]
    assert path.max_step_wait_seconds == 15


def test_navigation_path_matches_accents_case_and_spaces() -> None:
    path = NavigationPath.default()

    assert path.matches("Homologacao de Ponto Eletronico", "Homologação de Ponto Eletrônico")
    assert path.matches("Relatorio", "  relatório  ")
    assert not path.matches("Espelho do Ponto", "Relatorio de Ponto")
