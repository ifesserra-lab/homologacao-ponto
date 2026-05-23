COMPLETED_SELECTION_RESULT = {
    "run_id": "selection-completed",
    "completed_at": "2026-05-20T12:00:00+00:00",
    "username_ref": "paulo",
    "requested_server": "Celio Proliciano Maioli",
    "selected_server": "CELIO PROLICIANO MAIOLI",
    "selected_identifier": "1534589",
    "status": "completed",
    "success": True,
    "final_step": "Servidor Selecionado",
    "message": "servidor selecionado",
}

FAILED_SELECTION_RESULT = {
    "run_id": "selection-failed",
    "completed_at": "2026-05-20T12:00:00+00:00",
    "username_ref": "paulo",
    "requested_server": "Servidor Ausente",
    "status": "failed",
    "success": False,
    "final_step": "Busca de Servidor",
    "message": "servidor não encontrado: Servidor Ausente",
}

PARTIAL_SELECTION_RESULT = {
    "run_id": "selection-partial",
    "completed_at": "2026-05-20T12:00:00+00:00",
    "username_ref": "paulo",
    "requested_server": "Celio Proliciano Maioli",
    "status": "partial",
    "success": False,
    "final_step": "Selecionar Servidor",
    "message": "BrowserSession expirada durante a seleção do servidor",
}

BLOCKED_SELECTION_RESULT = {
    "run_id": "selection-blocked",
    "completed_at": "2026-05-20T12:00:00+00:00",
    "username_ref": "paulo",
    "requested_server": "Celio Proliciano Maioli",
    "status": "blocked",
    "success": False,
    "final_step": "Selecionar Servidor",
    "message": "proteção anti-automação impede a automação",
}
