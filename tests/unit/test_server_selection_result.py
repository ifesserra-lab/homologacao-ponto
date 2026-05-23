import pytest

from homologacao_ponto.models import SelecaoServidorResult, SelectionStatus


def test_selection_result_completed_serializes_success_fields() -> None:
    result = SelecaoServidorResult(
        username_ref="paulo",
        requested_server="Celio Proliciano Maioli",
        status=SelectionStatus.COMPLETED,
        final_step="Servidor Selecionado",
        selected_server="CELIO PROLICIANO MAIOLI",
        selected_identifier="1534589",
    )

    data = result.to_dict()

    assert data["status"] == "completed"
    assert data["success"] is True
    assert data["selected_server"] == "CELIO PROLICIANO MAIOLI"
    assert result.output_filename.startswith("selection-result-")


def test_selection_result_requires_message_for_unsuccessful_status() -> None:
    with pytest.raises(ValueError):
        SelecaoServidorResult(
            username_ref="paulo",
            requested_server="Celio Proliciano Maioli",
            status=SelectionStatus.FAILED,
            final_step="Busca de Servidor",
        )


def test_selection_result_completed_requires_selected_server() -> None:
    with pytest.raises(ValueError):
        SelecaoServidorResult(
            username_ref="paulo",
            requested_server="Celio Proliciano Maioli",
            status=SelectionStatus.COMPLETED,
            final_step="Servidor Selecionado",
        )
