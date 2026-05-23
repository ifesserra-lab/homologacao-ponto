import pytest
from homologacao_ponto.models.batch_config import BatchConfigLoader, BatchConfigError


def test_yaml_with_invalid_mes(tmp_path):
    f = tmp_path / "s.yaml"
    f.write_text("mes: 13\nservidores:\n  - nome: X\n    siape: '1'\n")
    # mes=13 inválido — BatchConfigLoader não valida range (Python nativo),
    # mas o campo é passado adiante. Verificar que carrega sem erro:
    cfg = BatchConfigLoader.load(f)
    assert cfg.mes == 13  # validação de range é responsabilidade do chamador


def test_yaml_missing_nome_raises(tmp_path):
    f = tmp_path / "s.yaml"
    f.write_text("servidores:\n  - siape: '123'\n")
    with pytest.raises(BatchConfigError):
        BatchConfigLoader.load(f)


def test_yaml_missing_siape_raises(tmp_path):
    f = tmp_path / "s.yaml"
    f.write_text("servidores:\n  - nome: CELIO\n")
    with pytest.raises(BatchConfigError):
        BatchConfigLoader.load(f)


def test_yaml_empty_nome_raises(tmp_path):
    f = tmp_path / "s.yaml"
    f.write_text("servidores:\n  - nome: ''\n    siape: '123'\n")
    with pytest.raises(BatchConfigError):
        BatchConfigLoader.load(f)
