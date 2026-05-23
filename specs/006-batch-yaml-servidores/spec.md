# Feature Specification: Lote de Servidores via Arquivo YAML

**Feature Branch**: `006-batch-yaml-servidores`
**Created**: 2026-05-23
**Status**: Draft
**EPIC**: EPIC-3 · Exportação do Espelho de Ponto

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Baixar espelho de múltiplos servidores via YAML (Priority: P1)

Usuário cria um arquivo YAML com lista de servidores (nome e SIAPE) e executa o comando. O sistema processa cada servidor sequencialmente, autentica uma vez, e salva o JSON de cada espelho em `data/servidores/{slug}/`.

**Why this priority**: Caso de uso principal da feature — sem isso não há valor entregue.

**Independent Test**: Dado arquivo YAML com 2 servidores válidos, o sistema cria 2 arquivos JSON em pastas distintas.

**Acceptance Scenarios**:

1. **Given** arquivo `servidores.yaml` com 2 entradas válidas, **When** `homologacao-ponto batch --file servidores.yaml`, **Then** 2 JSONs criados em `data/servidores/{slug}/espelho-{periodo}.json`
2. **Given** arquivo YAML com N servidores, **When** execução completa, **Then** relatório final mostra N linhas com status (sucesso/falha) por servidor
3. **Given** mês/ano não especificado no YAML, **When** execução, **Then** usa mês/ano corrente como padrão

---

### User Story 2 — Continuar lote após falha parcial (Priority: P2)

Se um servidor falhar (não encontrado, erro de rede, seleção inválida), o sistema registra o erro e continua processando os próximos servidores da lista.

**Why this priority**: Lista com 20 servidores não pode travar por um único erro — garante resiliência operacional.

**Independent Test**: Dado YAML com 3 servidores onde o 2° não existe no SIGRH, o 1° e 3° são exportados com sucesso e o 2° aparece como falha no relatório.

**Acceptance Scenarios**:

1. **Given** servidor não encontrado no SIGRH, **When** processando lista, **Then** registra `failed` para aquele servidor e continua para o próximo
2. **Given** sessão expirada durante lote, **When** detectada, **Then** reautentica e retoma a partir do servidor atual
3. **Given** lote completo com falhas parciais, **When** relatório gerado, **Then** exit code é não-zero para indicar falhas

---

### User Story 3 — Relatório consolidado do lote (Priority: P3)

Ao final do processamento, o sistema salva um arquivo JSON com resumo de todos os servidores processados: status, caminho do arquivo gerado, erros se houver.

**Why this priority**: Auditabilidade — permite verificar resultado sem abrir cada arquivo individualmente.

**Independent Test**: Dado lote de 3 servidores, após execução existe `data/runs/batch-result-{run_id}.json` com 3 entradas.

**Acceptance Scenarios**:

1. **Given** lote processado, **When** relatório consultado, **Then** contém: `servidor`, `siape`, `status`, `export_path` (ou null), `error` (ou null) para cada entrada
2. **Given** relatório gerado, **When** lido, **Then** inclui timestamp de início/fim e contagem total/sucesso/falha

---

### Edge Cases

- O que acontece se o arquivo YAML não existir ou estiver malformado?
- O que acontece se a lista estiver vazia?
- O que acontece se o mesmo servidor aparecer duas vezes na lista?
- O que acontece se o SIAPE informado não corresponder ao nome do servidor?

### Testability Requirements

- Cada user story deve ter teste independente antes do código de produção.
- Falhas de servidor individual, YAML inválido e sessão expirada devem ter cenários negativos.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Sistema DEVE aceitar caminho para arquivo YAML via argumento `--file` no subcomando `batch`
- **FR-002**: Arquivo YAML DEVE suportar lista de servidores com campos `nome`, `siape`, e opcionalmente `mes` e `ano`
- **FR-003**: Sistema DEVE processar servidores sequencialmente, autenticando uma única vez no início
- **FR-004**: Sistema DEVE continuar processamento após falha individual de servidor, sem abortar o lote
- **FR-005**: Sistema DEVE salvar JSON de cada servidor em `data/servidores/{slug}/espelho-{periodo}.json` (mesmo padrão da spec 005)
- **FR-006**: Sistema DEVE gerar relatório consolidado JSON ao final com status por servidor
- **FR-007**: Sistema DEVE exibir progresso no terminal durante execução (servidor atual / total)
- **FR-008**: Exit code DEVE ser não-zero se qualquer servidor falhou
- **FR-009**: Sistema DEVE reautenticar automaticamente se sessão expirar durante o lote
- **FR-010**: Arquivo YAML com lista vazia DEVE gerar erro com mensagem clara

### Formato do Arquivo YAML

```yaml
# servidores.yaml
mes: 5        # opcional — padrão: mês corrente
ano: 2026     # opcional — padrão: ano corrente
servidores:
  - nome: "CELIO PROLICIANO MAIOLI"
    siape: "1534589"
  - nome: "OUTRO SERVIDOR"
    siape: "9876543"
    mes: 4    # sobrescreve o padrão do arquivo
```

### Key Entities

- **BatchConfig**: arquivo YAML deserializado — lista de servidores + defaults de período
- **BatchEntry**: um servidor da lista — nome, siape, mes, ano
- **BatchResult**: relatório final — run_id, started_at, finished_at, total, succeeded, failed, entries
- **BatchEntryResult**: resultado por servidor — servidor, siape, status, export_path, error

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Lista com 10 servidores processada em menos de 5 minutos (headless)
- **SC-002**: Falha em servidor individual não interrompe processamento dos demais
- **SC-003**: 100% dos servidores bem-sucedidos possuem JSON válido em `data/servidores/{slug}/`
- **SC-004**: Relatório consolidado sempre gerado, mesmo em caso de falha total

## Assumptions

- Autenticação com as credenciais do `.env` é válida para todos os servidores da lista
- Servidores são processados um a um (sem paralelismo) para não sobrecarregar o SIGRH
- Período padrão (sem `mes`/`ano` no YAML) é o mês corrente
- Subcomando `batch` é independente do subcomando `espelho-ponto` existente
- Sessão Playwright é reutilizada entre servidores para reduzir overhead de login
