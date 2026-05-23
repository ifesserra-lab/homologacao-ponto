# Feature Specification: Dashboard de Espelhos de Ponto

**Feature Branch**: `008-dashboard-espelho-ponto`  
**Created**: 2026-05-23  
**Status**: Draft  
**Input**: Dashboard para visualizar de forma resumida os espelhos de cada servidor

## User Scenarios & Testing *(mandatory)*

### User Story 1 — Visão consolidada por servidor (Priority: P1)

O usuário abre o dashboard e vê uma lista de todos os servidores para os quais há espelhos exportados. Para cada servidor, a lista mostra o total de meses disponíveis, o intervalo de período coberto e um indicador rápido de status (todos homologados, algum pendente, algum vazio).

**Why this priority**: É o ponto de entrada do dashboard — sem ele nenhuma outra visualização faz sentido. Entrega valor imediato ao gestor que precisa saber quais servidores já foram processados.

**Independent Test**: Com os JSONs em `data/runs/servidores/`, abrir o dashboard e verificar que cada subpasta de servidor aparece como um card ou linha com o resumo correto.

**Acceptance Scenarios**:

1. **Given** há JSONs em `data/runs/servidores/celio-proliciano-maioli/`, **When** o dashboard é aberto, **Then** aparece um item para "CELIO PROLICIANO MAIOLI" com o número de espelhos disponíveis e o intervalo de período.
2. **Given** um servidor tem 5 espelhos (3 completed, 2 empty), **When** o item é exibido, **Then** o indicador de status mostra a distinção entre meses com registros e meses sem registros.
3. **Given** nenhum espelho existe em `data/runs/servidores/`, **When** o dashboard é aberto, **Then** é exibida mensagem informando que não há dados.

---

### User Story 2 — Detalhamento mensal de um servidor (Priority: P1)

O usuário seleciona um servidor e vê a lista de todos os meses disponíveis para aquele servidor. Para cada mês é exibido: período de referência, status, total de dias com marcação, total de créditos e débitos do mês, e DNC acumulado.

**Why this priority**: A seleção do servidor é o fluxo principal de uso — o gestor precisa navegar mês a mês para verificar situações específicas.

**Independent Test**: Selecionar o servidor e verificar que os dados do mês batem com os valores do JSON correspondente (`espelho-março-2026.json` etc.).

**Acceptance Scenarios**:

1. **Given** o servidor selecionado tem espelhos de janeiro a maio/2026, **When** o detalhe é aberto, **Then** aparecem 5 linhas uma por mês com período, status e métricas do mês.
2. **Given** um mês tem `status: empty`, **When** exibido na lista, **Then** é marcado visivelmente como "Sem registros" e não exibe métricas de horas.
3. **Given** um mês tem `status: completed`, **When** exibido, **Then** mostra: dias trabalhados, soma de HH, soma de crédito, soma de débito, DNC final do mês.

---

### User Story 3 — Detalhamento diário de um mês (Priority: P2)

O usuário seleciona um mês e vê a tabela completa de registros diários: data, dia da semana, marcações de ponto, HR, HC, HE, HA, HH, crédito, débito, saldo no mês e DNC.

**Why this priority**: Permite auditar dia a dia sem abrir o JSON manualmente. Necessário para análise aprofundada, mas o dashboard já entrega valor com US1 e US2 apenas.

**Independent Test**: Selecionar março/2026 do servidor Celio e verificar que a tabela bate registro a registro com o JSON `espelho-março-2026.json`.

**Acceptance Scenarios**:

1. **Given** o mês selecionado tem 31 linhas no JSON, **When** a tabela é exibida, **Then** aparecem exatamente 31 linhas na mesma ordem.
2. **Given** um dia tem marcações `["07:58","12:00","13:00","17:03"]`, **When** exibido, **Then** as marcações aparecem formatadas e legíveis.
3. **Given** um dia tem campo `dnc: "00:00"`, **When** exibido, **Then** o valor aparece como `00:00` (não como `null` ou vazio).
4. **Given** um campo é `null` no JSON (ex.: `ha: null`), **When** exibido, **Then** a célula aparece vazia ou com traço `—`, não com o texto "null".

---

### User Story 4 — Filtros e busca (Priority: P3)

O usuário pode filtrar a lista de servidores por nome e filtrar os meses por status (completed / empty) ou por intervalo de período.

**Why this priority**: Útil quando há múltiplos servidores, mas o dashboard já é funcional sem filtros para o caso de uso imediato (poucos servidores).

**Independent Test**: Com 3 servidores cadastrados, digitar parte do nome e verificar que a lista reduz ao servidor correto.

**Acceptance Scenarios**:

1. **Given** há 3 servidores, **When** o usuário digita "celio", **Then** apenas o servidor cujo nome contém "celio" (case-insensitive) permanece visível.
2. **Given** filtro por status "empty" está ativo, **When** aplicado na lista de meses de um servidor, **Then** apenas os meses sem registros são exibidos.

---

### Edge Cases

- Servidor com apenas um espelho disponível: exibir sem indicar "intervalo".
- JSON corrompido ou inválido na pasta: ignorar arquivo com aviso, não travar o dashboard.
- Campos de hora em formato inesperado (não `HH:MM`): exibir valor bruto sem crashar.
- Pasta `data/runs/servidores/` inexistente: exibir tela de estado vazio com instrução para rodar o batch.
- Múltiplos arquivos do mesmo mês (re-execuções): exibir o mais recente (maior `captured_at`).

### Testability Requirements

- Cada user story tem teste independente descrito acima.
- Leitura dos JSONs deve ter teste negativo: arquivo ausente, JSON malformado, campo faltante.
- A agregação de métricas mensais (soma de crédito, débito, contagem de dias) deve ser testável isolada da interface.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O dashboard DEVE ler os JSONs de espelho a partir de `data/runs/servidores/` sem necessidade de configuração adicional.
- **FR-002**: O dashboard DEVE exibir um resumo por servidor com: nome, número de meses disponíveis, intervalo de período e indicador de status.
- **FR-003**: O dashboard DEVE permitir navegar para o detalhe de um servidor, exibindo a lista de meses com métricas mensais agregadas.
- **FR-004**: O dashboard DEVE permitir navegar para o detalhe de um mês, exibindo a tabela completa de registros diários conforme o schema `docs/espelho-ponto-schema.yaml`.
- **FR-005**: O dashboard DEVE exibir os campos de horas com seus nomes completos: HR (Horas Registradas), HC (Horas Contabilizadas), HE (Horas Excedentes), HA (Horas Autorizadas), HH (Horas Homologadas), DNC (Débito Não Compensado).
- **FR-006**: Campos `null` no JSON DEVEM ser exibidos como célula vazia ou traço `—`, nunca como o texto "null".
- **FR-007**: O dashboard DEVE tratar JSONs inválidos ou ausentes sem interromper a exibição dos demais arquivos válidos.
- **FR-008**: O dashboard DEVE exibir o mês mais recente quando houver múltiplos arquivos para o mesmo período de referência.
- **FR-009**: O dashboard DEVE ser acessível via linha de comando ou navegador sem servidor externo (arquivo local ou servidor embutido leve).
- **FR-010**: O usuário DEVE poder filtrar servidores por nome (busca textual, case-insensitive).

### Key Entities

- **Servidor**: Agrega todos os espelhos de um servidor pelo slug do nome; atributos derivados: nome canônico, SIAPE, lista de períodos.
- **EspelhoMes**: Um arquivo JSON de espelho para um período; atributos: período de referência, status, `captured_at`, lista de registros diários.
- **RegistroDia**: Uma linha da tabela do espelho; atributos: data, dia_semana, marcações, HR, HC, HE, HA, HH, crédito, débito, saldo_no_mes, credito_acumulado, DNC.
- **ResumoMes**: Agregação calculada a partir de um `EspelhoMes`: total de dias com marcação, soma de crédito, soma de débito, DNC do último dia, contagem de dias `empty`.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: O gestor visualiza o resumo de todos os servidores em menos de 3 segundos após abrir o dashboard, independentemente do número de espelhos disponíveis.
- **SC-002**: Navegar do resumo de servidor até a tabela diária de um mês requer no máximo 2 interações (cliques ou comandos).
- **SC-003**: 100% dos campos do JSON são exibidos na interface — nenhum campo do schema é omitido na visão detalhada.
- **SC-004**: JSONs corrompidos não causam falha total — o dashboard exibe os demais servidores normalmente e indica quais arquivos foram ignorados.
- **SC-005**: A agregação mensal (soma de crédito/débito, contagem de dias) é verificavelmente correta contra os valores brutos do JSON.

## Assumptions

- Os JSONs seguem o schema documentado em `docs/espelho-ponto-schema.yaml` (schema_version: 1).
- O dashboard é para uso interno/local — não há requisitos de autenticação ou multi-usuário.
- O volume de dados é pequeno a médio (dezenas de servidores, até 12 meses cada) — performance não é crítica.
- Interface web local (HTML/CSS/JS sem framework pesado) ou TUI é aceitável; não é necessário servidor remoto.
- A pasta `data/runs/servidores/` é a única fonte de dados — não há banco de dados externo.
- O campo `credito_acumulado` do último registro do mês representa o banco de horas ao final do período.
