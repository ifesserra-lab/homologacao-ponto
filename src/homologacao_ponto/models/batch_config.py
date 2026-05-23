from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path

import yaml


class BatchConfigError(ValueError):
    """Sinaliza configuração inválida de batch.

    Herda de ValueError para que chamadores possam capturar erros de entrada
    com ``except ValueError`` sem depender deste módulo diretamente.
    """


@dataclass(frozen=True)
class BatchEntry:
    nome: str
    siape: str
    mes: int | None = None
    ano: int | None = None


@dataclass(frozen=True)
class BatchConfig:
    servidores: list[BatchEntry]
    mes: int | None = None
    ano: int | None = None


class BatchConfigLoader:
    @staticmethod
    def load(path: Path) -> BatchConfig:
        """Lê e valida o arquivo YAML de configuração de batch.

        Usa ``yaml.safe_load`` em vez de ``yaml.load`` para bloquear execução
        arbitrária de Python embutida no YAML (exploit via construtores PyYAML).

        A validação de ``nome``/``siape`` ocorre aqui, não no dataclass, porque
        ``BatchEntry`` é frozen e não possui lógica de conversão de tipo (e.g.,
        ``siape`` vem como int do YAML e precisa ser str).
        """
        try:
            text = Path(path).read_text(encoding="utf-8")
        except OSError as exc:
            raise BatchConfigError(f"arquivo YAML não encontrado: {exc}") from exc
        try:
            data = yaml.safe_load(text)
        except yaml.YAMLError as exc:
            raise BatchConfigError(f"YAML inválido: {exc}") from exc
        if not isinstance(data, dict) or "servidores" not in data:
            raise BatchConfigError("campo 'servidores' obrigatório no YAML")
        raw = data.get("servidores") or []
        if not raw:
            raise BatchConfigError("lista de servidores não pode estar vazia")
        entries = []
        for i, item in enumerate(raw):
            if not isinstance(item, dict):
                raise BatchConfigError(f"entrada {i} inválida")
            nome = item.get("nome", "").strip()
            siape = str(item.get("siape", "")).strip()
            if not nome or not siape:
                raise BatchConfigError(f"entrada {i}: 'nome' e 'siape' obrigatórios")
            entries.append(
                BatchEntry(
                    nome=nome,
                    siape=siape,
                    mes=item.get("mes"),
                    ano=item.get("ano"),
                )
            )
        return BatchConfig(
            servidores=entries,
            mes=data.get("mes"),
            ano=data.get("ano"),
        )
