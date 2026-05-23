import pytest
from pathlib import Path

from homologacao_ponto.models.batch_config import BatchConfigError, BatchConfigLoader


def _write_yaml(tmp_path: Path, content: str) -> Path:
    p = tmp_path / "batch.yaml"
    p.write_text(content)
    return p


def test_load_anos_list(tmp_path):
    p = _write_yaml(
        tmp_path, "anos: [2025, 2026]\nservidores:\n  - nome: CELIO\n    siape: '123'\n"
    )
    cfg = BatchConfigLoader.load(p)
    assert cfg.anos == [2025, 2026]


def test_load_anos_all_uppercase(tmp_path):
    p = _write_yaml(
        tmp_path, "anos: All\nservidores:\n  - nome: CELIO\n    siape: '123'\n"
    )
    cfg = BatchConfigLoader.load(p)
    assert cfg.anos == "All"


def test_load_anos_all_lowercase_normalized(tmp_path):
    p = _write_yaml(
        tmp_path, "anos: all\nservidores:\n  - nome: CELIO\n    siape: '123'\n"
    )
    cfg = BatchConfigLoader.load(p)
    assert cfg.anos == "All"


def test_load_anos_empty_list_raises(tmp_path):
    p = _write_yaml(
        tmp_path, "anos: []\nservidores:\n  - nome: CELIO\n    siape: '123'\n"
    )
    with pytest.raises(BatchConfigError, match="anos"):
        BatchConfigLoader.load(p)


def test_load_anos_invalid_string_raises(tmp_path):
    p = _write_yaml(
        tmp_path, "anos: \"Invalido\"\nservidores:\n  - nome: CELIO\n    siape: '123'\n"
    )
    with pytest.raises(BatchConfigError):
        BatchConfigLoader.load(p)


def test_load_anos_out_of_range_raises(tmp_path):
    p = _write_yaml(
        tmp_path, "anos: [1900]\nservidores:\n  - nome: CELIO\n    siape: '123'\n"
    )
    with pytest.raises(BatchConfigError):
        BatchConfigLoader.load(p)


def test_load_anos_string_in_list_raises(tmp_path):
    p = _write_yaml(
        tmp_path,
        "anos: [\"x\", 2025]\nservidores:\n  - nome: CELIO\n    siape: '123'\n",
    )
    with pytest.raises(BatchConfigError):
        BatchConfigLoader.load(p)


def test_load_anos_duplicates_deduplicated(tmp_path):
    p = _write_yaml(
        tmp_path,
        "anos: [2025, 2025, 2026]\nservidores:\n  - nome: CELIO\n    siape: '123'\n",
    )
    cfg = BatchConfigLoader.load(p)
    assert cfg.anos == [2025, 2026]


def test_load_anos_coexists_with_mes_ano_no_error(tmp_path):
    p = _write_yaml(
        tmp_path,
        "anos: [2025]\nmes: 5\nano: 2026\nservidores:\n  - nome: CELIO\n    siape: '123'\n",
    )
    cfg = BatchConfigLoader.load(p)
    assert cfg.anos == [2025]
    assert cfg.mes == 5
    assert cfg.ano == 2026


def test_load_no_anos_is_none(tmp_path):
    p = _write_yaml(
        tmp_path, "mes: 5\nano: 2026\nservidores:\n  - nome: CELIO\n    siape: '123'\n"
    )
    cfg = BatchConfigLoader.load(p)
    assert cfg.anos is None


def test_load_anos_sorted(tmp_path):
    p = _write_yaml(
        tmp_path,
        "anos: [2026, 2024, 2025]\nservidores:\n  - nome: CELIO\n    siape: '123'\n",
    )
    cfg = BatchConfigLoader.load(p)
    assert cfg.anos == [2024, 2025, 2026]
