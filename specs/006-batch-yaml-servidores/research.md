# Research: Lote de Servidores via Arquivo YAML

**Branch**: `006-batch-yaml-servidores` | **Date**: 2026-05-23

## Decisão 1 — Parser YAML

**Decision**: `PyYAML` (já disponível como dependência transitiva do Playwright) ou stdlib `tomllib` — usar PyYAML via `yaml.safe_load()`.
**Rationale**: PyYAML é a biblioteca padrão Python para YAML; `safe_load` evita execução de código arbitrário; já consta no ambiente.
**Alternatives considered**: `ruamel.yaml` (mais pesada, não necessária para YAML simples); `tomllib` (formato TOML, não YAML).

## Decisão 2 — Estrutura do Batch no `app.py`

**Decision**: Novo método `run_batch()` em `HomologacaoPontoApp` que aceita lista de `BatchEntry` e itera chamando a lógica interna de seleção+exportação sem fechar/reabrir browser entre servidores.
**Rationale**: Reutiliza todo o fluxo já testado de `run_espelho_ponto()`. Login único, Playwright context compartilhado, `SigrhBrowser` permanece aberto durante o lote.
**Alternatives considered**: Novo `App` dedicado (duplicação); múltiplos processos independentes (overhead de login N vezes).

## Decisão 3 — Modelo de dados do YAML

**Decision**: Dataclass `BatchConfig(mes, ano, servidores: list[BatchEntry])` e `BatchEntry(nome, siape, mes, ano)`. Mes/ano no entry sobrescreve o default do config. Todos opcionais com `None` = mês/ano corrente.
**Rationale**: Frozen dataclasses seguem convenção do projeto (Constitution III). Separação clara entre defaults globais e overrides por servidor.
**Alternatives considered**: Dict direto sem dataclass (não testável, sem type safety).

## Decisão 4 — Relatório do Lote

**Decision**: `BatchResult` dataclass com `run_id`, `started_at`, `finished_at`, `entries: list[BatchEntryResult]`. Persistido via `ResultWriter` como `batch-result-{run_id}.json` em `output_dir` (flat, sem subdir).
**Rationale**: Mesmo contrato de `ResultWriter` existente. `getattr(result, "output_subdir", None)` já faz fallback para flat path.
**Alternatives considered**: Múltiplos JSONs separados (já existem — este é o resumo); log para stdout apenas (não auditável).

## Decisão 5 — Reautenticação durante lote

**Decision**: Detectar `ExportStatus.BLOCKED` / `NavigationStatus.BLOCKED` com `error_code == "session_expired"` dentro do loop. Reautenticar e repetir o servidor atual (máximo 1 retry).
**Rationale**: Padrão já usado em `app.py` para sessão expirada; não requer nova abstração.
**Alternatives considered**: Reautenticação proativa a cada N servidores (overhead desnecessário).

## Decisão 6 — CLI: subcomando `batch`

**Decision**: `homologacao-ponto batch --file servidores.yaml [--mes M] [--ano A] [--output-dir DIR] [--env-file FILE]`. Flags `--mes`/`--ano` CLI sobrescrevem defaults do YAML.
**Rationale**: Consistente com `espelho-ponto`. Flags CLI > YAML file > mês/ano corrente.
**Alternatives considered**: Ler YAML e ignorar flags CLI (menos flexível).

## Dependências Identificadas

| Componente | Já existe? | Ação |
|------------|-----------|------|
| `PyYAML` | Verificar `pyproject.toml` | Adicionar se ausente |
| `BatchConfig`, `BatchEntry` | Não | Criar em `models/batch_config.py` |
| `BatchResult`, `BatchEntryResult` | Não | Criar em `models/batch_result.py` |
| `BatchService` | Não | Criar em `services/batch_service.py` |
| `HomologacaoPontoApp.run_batch()` | Não | Adicionar em `app.py` |
| CLI subcomando `batch` | Não | Adicionar em `cli.py` |
| `ResultWriter.write()` | Existe | Sem mudança — `BatchResult` sem `output_subdir` → flat path |
