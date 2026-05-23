from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path


def _slug(name: str) -> str:
    nfkd = unicodedata.normalize("NFD", name)
    ascii_only = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", ascii_only.lower()).strip("-")


def _periodo_slug(periodo: str | None, run_id: str) -> str:
    if periodo:
        return periodo.lower().replace("/", "-")
    return run_id


@dataclass(frozen=True)
class ServidorSelecionado:
    nome: str
    identificador: str | None = None
    texto_visivel: str | None = None

    def __post_init__(self) -> None:
        if not self.nome and not self.texto_visivel:
            raise ValueError("nome or texto_visivel is required")

    def to_dict(self) -> dict[str, str | None]:
        return {
            "nome": self.nome,
            "identificador": self.identificador,
            "texto_visivel": self.texto_visivel,
        }


@dataclass(frozen=True)
class RegistroDiaPonto:
    data: str
    dia_semana: str | None = None
    marcacoes: list[str] = field(default_factory=list)
    ocorrencias: list[str] = field(default_factory=list)
    observacoes: list[str] = field(default_factory=list)
    situacao: str | None = None
    textos_visiveis: list[str] = field(default_factory=list)
    hr: str | None = None
    hc: str | None = None
    he: str | None = None
    ha: str | None = None
    hh: str | None = None
    credito: str | None = None
    debito: str | None = None
    saldo_no_mes: str | None = None
    credito_acumulado: str | None = None
    dnc: str | None = None

    def __post_init__(self) -> None:
        if not any(
            [
                self.data,
                self.marcacoes,
                self.ocorrencias,
                self.observacoes,
                self.situacao,
                self.textos_visiveis,
            ]
        ):
            raise ValueError("registro requires visible data")

    def to_dict(self) -> dict[str, object]:
        return {
            "data": self.data,
            "dia_semana": self.dia_semana,
            "marcacoes": self.marcacoes,
            "ocorrencias": self.ocorrencias,
            "observacoes": self.observacoes,
            "situacao": self.situacao,
            "textos_visiveis": self.textos_visiveis,
            "hr": self.hr,
            "hc": self.hc,
            "he": self.he,
            "ha": self.ha,
            "hh": self.hh,
            "credito": self.credito,
            "debito": self.debito,
            "saldo_no_mes": self.saldo_no_mes,
            "credito_acumulado": self.credito_acumulado,
            "dnc": self.dnc,
        }


@dataclass(frozen=True)
class EspelhoPontoExport:
    run_id: str
    captured_at: str
    servidor: ServidorSelecionado
    registros: list[RegistroDiaPonto] = field(default_factory=list)
    periodo_referencia: str | None = None
    mensagens: list[str] = field(default_factory=list)
    status: str = "completed"
    pagina: str | None = None
    rotulos_visiveis: list[str] = field(default_factory=lambda: ["Espelho de Ponto"])
    output_path: str | None = None

    def __post_init__(self) -> None:
        if not self.run_id:
            raise ValueError("run_id is required")
        if not self.captured_at:
            raise ValueError("captured_at is required")
        if self.status not in {"completed", "empty"}:
            raise ValueError("invalid export status")
        if self.status == "completed" and not self.registros:
            raise ValueError("completed export requires registros")

    @classmethod
    def empty(
        cls,
        run_id: str,
        captured_at: str,
        servidor: ServidorSelecionado,
        periodo_referencia: str | None = None,
        mensagens: list[str] | None = None,
        pagina: str | None = None,
    ) -> EspelhoPontoExport:
        return cls(
            run_id=run_id,
            captured_at=captured_at,
            servidor=servidor,
            periodo_referencia=periodo_referencia,
            mensagens=mensagens or [],
            registros=[],
            status="empty",
            pagina=pagina,
        )

    @property
    def output_subdir(self) -> str:
        return f"servidores/{_slug(self.servidor.nome)}"

    @property
    def output_filename(self) -> str:
        return f"espelho-{_periodo_slug(self.periodo_referencia, self.run_id)}.json"

    def with_output_path(self, output_path: Path) -> EspelhoPontoExport:
        return EspelhoPontoExport(
            run_id=self.run_id,
            captured_at=self.captured_at,
            servidor=self.servidor,
            registros=self.registros,
            periodo_referencia=self.periodo_referencia,
            mensagens=self.mensagens,
            status=self.status,
            pagina=self.pagina,
            rotulos_visiveis=self.rotulos_visiveis,
            output_path=str(output_path),
        )

    def to_dict(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "run_id": self.run_id,
            "captured_at": self.captured_at or datetime.now(timezone.utc).isoformat(),
            "status": self.status,
            "servidor": self.servidor.to_dict(),
            "periodo_referencia": self.periodo_referencia,
            "mensagens": self.mensagens,
            "registros": [registro.to_dict() for registro in self.registros],
            "fonte": {
                "tipo": "sigrh-espelho-ponto-visivel",
                "pagina": self.pagina,
                "rotulos_visiveis": self.rotulos_visiveis,
            },
        }
