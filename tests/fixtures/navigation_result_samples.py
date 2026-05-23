COMPLETED_NAVIGATION_RESULT = {
    "run_id": "run-1",
    "completed_at": "2026-05-20T12:00:00+00:00",
    "username_ref": "paulo",
    "status": "completed",
    "success": True,
    "final_step": "Espelho do Ponto",
    "message": "navegação concluída",
    "steps": [
        {"label": "Chefia de Unidade", "position": 1, "status": "hovered"},
        {"label": "Homologacao de Ponto Eletronico", "position": 2, "status": "hovered"},
        {"label": "Relatorio", "position": 3, "status": "hovered"},
        {"label": "Espelho do Ponto", "position": 4, "status": "clicked"},
    ],
}

FAILED_NAVIGATION_RESULT = {
    "run_id": "run-2",
    "completed_at": "2026-05-20T12:00:00+00:00",
    "username_ref": "paulo",
    "status": "failed",
    "success": False,
    "final_step": "Homologacao de Ponto Eletronico",
    "message": "menu não encontrado: Homologacao de Ponto Eletronico",
    "steps": [
        {"label": "Chefia de Unidade", "position": 1, "status": "hovered"},
        {
            "label": "Homologacao de Ponto Eletronico",
            "position": 2,
            "status": "missing",
            "message": "menu não encontrado",
        },
    ],
}

PARTIAL_NAVIGATION_RESULT = {
    "run_id": "run-3",
    "completed_at": "2026-05-20T12:00:00+00:00",
    "username_ref": "paulo",
    "status": "partial",
    "success": False,
    "final_step": "Relatorio",
    "message": "BrowserSession expirada durante a navegação",
    "steps": [
        {"label": "Chefia de Unidade", "position": 1, "status": "hovered"},
        {"label": "Homologacao de Ponto Eletronico", "position": 2, "status": "hovered"},
        {"label": "Relatorio", "position": 3, "status": "expired", "message": "sessão expirada"},
    ],
}

BLOCKED_NAVIGATION_RESULT = {
    "run_id": "run-4",
    "completed_at": "2026-05-20T12:00:00+00:00",
    "username_ref": "paulo",
    "status": "blocked",
    "success": False,
    "final_step": "Chefia de Unidade",
    "message": "proteção anti-automação impede a automação",
    "steps": [
        {
            "label": "Chefia de Unidade",
            "position": 1,
            "status": "blocked",
            "message": "proteção anti-automação",
        }
    ],
}
