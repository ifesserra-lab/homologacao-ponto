import json
from pathlib import Path


from homologacao_ponto.models.espelho_ponto_export import (
    EspelhoPontoExport,
    RegistroDiaPonto,
    ServidorSelecionado,
)
from homologacao_ponto.services.result_writer import ResultWriter


def _make_export(nome="CELIO PROLICIANO MAIOLI", periodo="Dezembro/2025", run_id="inttest"):
    servidor = ServidorSelecionado(nome=nome)
    registro = RegistroDiaPonto(data="2025-12-15", marcacoes=["10:56"])
    return EspelhoPontoExport(
        run_id=run_id,
        captured_at="2026-05-23T00:00:00+00:00",
        servidor=servidor,
        registros=[registro],
        periodo_referencia=periodo,
    )


def test_espelho_writes_to_servidor_subdir(tmp_path):
    writer = ResultWriter(tmp_path)
    export = _make_export()
    persisted = writer.write(export)
    expected = tmp_path / "servidores" / "celio-proliciano-maioli" / "espelho-dezembro-2025.json"
    assert expected.exists(), f"File not found at {expected}"
    assert persisted.output_path == str(expected)


def test_espelho_subdir_created_automatically(tmp_path):
    writer = ResultWriter(tmp_path)
    export = _make_export(nome="JOSE SILVA", periodo="Maio/2026", run_id="abc")
    writer.write(export)
    assert (tmp_path / "servidores" / "jose-silva").is_dir()


def test_espelho_rerun_overwrites_not_duplicates(tmp_path):
    writer = ResultWriter(tmp_path)
    export = _make_export()
    writer.write(export)
    writer.write(export)
    files = list((tmp_path / "servidores" / "celio-proliciano-maioli").iterdir())
    assert len(files) == 1, f"Expected 1 file, found {len(files)}"


def test_two_servers_separate_subdirs(tmp_path):
    writer = ResultWriter(tmp_path)
    writer.write(_make_export(nome="SERVIDOR A", run_id="aaa"))
    writer.write(_make_export(nome="SERVIDOR B", run_id="bbb"))
    assert (tmp_path / "servidores" / "servidor-a").is_dir()
    assert (tmp_path / "servidores" / "servidor-b").is_dir()


def test_espelho_json_content_valid(tmp_path):
    writer = ResultWriter(tmp_path)
    persisted = writer.write(_make_export())
    data = json.loads(Path(persisted.output_path).read_text())
    assert data["status"] == "completed"
    assert data["servidor"]["nome"] == "CELIO PROLICIANO MAIOLI"
