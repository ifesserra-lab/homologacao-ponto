# Data Model: Lote de Servidores via Arquivo YAML

**Branch**: `006-batch-yaml-servidores` | **Date**: 2026-05-23

## Entidades Novas

### `BatchEntry`

Representa um servidor na lista do YAML.

```python
@dataclass(frozen=True)
class BatchEntry:
    nome: str                  # Nome do servidor — ex: "CELIO PROLICIANO MAIOLI"
    siape: str                 # Matrícula SIAPE — ex: "1534589"
    mes: int | None = None     # Sobrescreve default do BatchConfig
    ano: int | None = None     # Sobrescreve default do BatchConfig
```

### `BatchConfig`

Configuração completa deserializada do arquivo YAML.

```python
@dataclass(frozen=True)
class BatchConfig:
    servidores: list[BatchEntry]
    mes: int | None = None     # Default de período para todos os servidores
    ano: int | None = None     # Default de período para todos os servidores
```

### `BatchEntryResult`

Resultado do processamento de um servidor individual no lote.

```python
@dataclass(frozen=True)
class BatchEntryResult:
    nome: str
    siape: str
    status: str                # "completed" | "empty" | "failed" | "blocked"
    export_path: str | None    # Caminho do JSON gerado, ou None se falhou
    error: str | None          # Mensagem de erro, ou None se sucesso

    def to_dict(self) -> dict: ...
```

### `BatchResult`

Relatório consolidado do lote — persistido como `batch-result-{run_id}.json`.

```python
@dataclass(frozen=True)
class BatchResult:
    run_id: str
    started_at: str            # ISO 8601
    finished_at: str           # ISO 8601
    total: int
    succeeded: int
    failed: int
    entries: list[BatchEntryResult]

    # Sem output_subdir → ResultWriter escreve em flat output_dir/
    @property
    def output_filename(self) -> str:
        return f"batch-result-{self.run_id}.json"

    def with_output_path(self, path: Path) -> "BatchResult": ...
    def to_dict(self) -> dict: ...
```

## Serviço Novo

### `BatchService`

Orquestra o processamento sequencial do lote. Recebe `HomologacaoPontoApp` (ou os serviços internos) e itera sobre os `BatchEntry`.

```python
class BatchService:
    def __init__(self, app: HomologacaoPontoApp, result_writer: ResultWriter) -> None: ...

    def run(self, session: BrowserSession, config: BatchConfig, run_id: str) -> BatchResult: ...
```

**Fluxo interno de `run()`**:
1. Para cada `BatchEntry`: resolve `mes`/`ano` (entry > config > corrente)
2. Chama `app._run_single_espelho(session, entry, mes, ano)` — método interno extraído de `run_espelho_ponto()`
3. Captura `AppResult` → converte em `BatchEntryResult`
4. Se `error_code == "session_expired"` → reautentica e retenta (1x)
5. Retorna `BatchResult` com todas as entradas

## Mudanças em Entidades Existentes

### `HomologacaoPontoApp`

Extrai lógica de seleção+exportação de `run_espelho_ponto()` em método interno reutilizável:

```python
def _run_single_espelho(
    self,
    session: BrowserSession,
    servidor: str,
    siape: str,
    mes: int | None,
    ano: int | None,
) -> AppResult: ...
```

`run_espelho_ponto()` passa a delegar para `_run_single_espelho()` — sem mudança de comportamento externo.

### `cli.py`

Novo subcomando `batch`:

```python
batch = subcommands.add_parser("batch")
batch.add_argument("--file", required=True)
batch.add_argument("--output-dir", default="./data/runs")
batch.add_argument("--env-file", default=".env")
batch.add_argument("--mes", type=int, choices=range(1, 13), metavar="{1..12}")
batch.add_argument("--ano", type=int)
```

## Arquivo YAML — Schema

```yaml
# Campos top-level (opcionais — padrão: mês/ano corrente)
mes: 5
ano: 2026

servidores:
  - nome: "CELIO PROLICIANO MAIOLI"
    siape: "1534589"
  - nome: "OUTRO SERVIDOR"
    siape: "9876543"
    mes: 4        # override por servidor
    ano: 2026
```

**Regras de validação**:
- `servidores` obrigatório e não-vazio
- Cada entry: `nome` (str não-vazio) e `siape` (str não-vazio) obrigatórios
- `mes` 1..12 se presente; `ano` >= 2000 se presente

## Novos Arquivos

```text
src/homologacao_ponto/models/batch_config.py    # BatchEntry, BatchConfig
src/homologacao_ponto/models/batch_result.py    # BatchEntryResult, BatchResult
src/homologacao_ponto/services/batch_service.py  # BatchService

tests/unit/test_batch_config.py
tests/unit/test_batch_result.py
tests/unit/test_batch_service.py
tests/integration/test_batch_end_to_end.py
tests/fixtures/batch_fixtures.py
```
