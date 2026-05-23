import pytest
from pathlib import Path
from homologacao_ponto.models.batch_config import BatchConfigLoader, BatchConfigError

def test_load_valid_yaml(tmp_path):
    f = tmp_path / "s.yaml"
    f.write_text("mes: 5\nano: 2026\nservidores:\n  - nome: CELIO\n    siape: '123'\n")
    cfg = BatchConfigLoader.load(f)
    assert cfg.mes == 5
    assert cfg.ano == 2026
    assert len(cfg.servidores) == 1
    assert cfg.servidores[0].nome == "CELIO"
    assert cfg.servidores[0].siape == "123"

def test_entry_mes_ano_optional(tmp_path):
    f = tmp_path / "s.yaml"
    f.write_text("servidores:\n  - nome: X\n    siape: '1'\n")
    cfg = BatchConfigLoader.load(f)
    assert cfg.mes is None
    assert cfg.ano is None
    assert cfg.servidores[0].mes is None
    assert cfg.servidores[0].ano is None

def test_entry_override_mes_ano(tmp_path):
    f = tmp_path / "s.yaml"
    f.write_text("mes: 5\nano: 2026\nservidores:\n  - nome: X\n    siape: '1'\n    mes: 4\n    ano: 2025\n")
    cfg = BatchConfigLoader.load(f)
    assert cfg.servidores[0].mes == 4
    assert cfg.servidores[0].ano == 2025

def test_malformed_yaml_raises(tmp_path):
    f = tmp_path / "s.yaml"
    f.write_text("servidores:\n  - nome: [unclosed\n")
    with pytest.raises(BatchConfigError):
        BatchConfigLoader.load(f)

def test_empty_servers_raises(tmp_path):
    f = tmp_path / "s.yaml"
    f.write_text("servidores: []\n")
    with pytest.raises(BatchConfigError, match="vazia"):
        BatchConfigLoader.load(f)

def test_missing_servers_raises(tmp_path):
    f = tmp_path / "s.yaml"
    f.write_text("mes: 5\n")
    with pytest.raises(BatchConfigError, match="servidores"):
        BatchConfigLoader.load(f)

def test_file_not_found_raises():
    with pytest.raises(BatchConfigError):
        BatchConfigLoader.load(Path("/nao/existe.yaml"))
