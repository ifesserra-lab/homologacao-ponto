from __future__ import annotations

import json
from pathlib import Path


CONTRACTS_DIR = Path(__file__).parents[2] / "specs" / "004-baixar-espelho-json" / "contracts"


def load_contract_schema(name: str) -> dict[str, object]:
    return json.loads((CONTRACTS_DIR / name).read_text(encoding="utf-8"))


def sample_export_dict() -> dict[str, object]:
    return {
        "schema_version": 1,
        "run_id": "run-123",
        "captured_at": "2026-05-20T12:00:00+00:00",
        "status": "completed",
        "servidor": {
            "nome": "CELIO PROLICIANO MAIOLI",
            "identificador": "1534589",
            "texto_visivel": "Servidor: CELIO PROLICIANO MAIOLI SIAPE: 1534589",
        },
        "periodo_referencia": "Maio/2026",
        "mensagens": ["Espelho gerado com sucesso"],
        "registros": [
            {
                "data": "2026-05-02",
                "dia_semana": "Sabado",
                "marcacoes": ["07:58", "12:00", "13:00", "17:03"],
                "ocorrencias": ["Trabalho presencial"],
                "observacoes": ["Sem pendencias"],
                "situacao": "Homologado",
                "textos_visiveis": ["Credito 00:05"],
            }
        ],
        "fonte": {
            "tipo": "sigrh-espelho-ponto-visivel",
            "pagina": "/sigrh/frequencia/espelho.jsf",
            "rotulos_visiveis": ["Espelho de Ponto"],
        },
    }


def sample_result_dict() -> dict[str, object]:
    return {
        "schema_version": 1,
        "run_id": "run-123",
        "started_at": "2026-05-20T12:00:00+00:00",
        "completed_at": "2026-05-20T12:00:01+00:00",
        "success": True,
        "status": "completed",
        "final_step": "Espelho Exportado",
        "requested_server": "Celio Proliciano Maioli",
        "selected_server": {
            "nome": "CELIO PROLICIANO MAIOLI",
            "identificador": "1534589",
            "texto_visivel": "Servidor: CELIO PROLICIANO MAIOLI SIAPE: 1534589",
        },
        "periodo_referencia": "Maio/2026",
        "export_path": "data/runs/espelho-ponto-run-123.json",
        "message": "Espelho de Ponto exportado com sucesso",
        "error_code": None,
    }
