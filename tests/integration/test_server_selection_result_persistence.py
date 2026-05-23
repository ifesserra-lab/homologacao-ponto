from homologacao_ponto.models import SelecaoServidorResult, SelectionStatus
from homologacao_ponto.services.result_writer import ResultWriter


def test_selection_result_persistence_for_success_and_failure(tmp_path) -> None:
    writer = ResultWriter(tmp_path)
    success = writer.write(
        SelecaoServidorResult(
            "paulo",
            "Celio Proliciano Maioli",
            SelectionStatus.COMPLETED,
            "Servidor Selecionado",
            selected_server="CELIO PROLICIANO MAIOLI",
        )
    )
    failure = writer.write(
        SelecaoServidorResult(
            "paulo",
            "Servidor Ausente",
            SelectionStatus.FAILED,
            "Busca de Servidor",
            message="servidor não encontrado: Servidor Ausente",
        )
    )

    assert (tmp_path / success.output_filename).exists()
    assert (tmp_path / failure.output_filename).exists()
