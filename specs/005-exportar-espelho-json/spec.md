# Feature Specification: Exportar Tabela Completa do Espelho de Ponto por Servidor

**Feature Branch**: `005-exportar-espelho-json`  
**Created**: 2026-05-23  
**Status**: Draft  
**Input**: User description: "após entrar no site do espelho de ponto, baixar a tabela Espelho de Ponto e salvar em json em uma pasta por pessoa"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Capturar tabela completa com campos calculados (Priority: P1)

Como gestor que precisa auditar o ponto de um servidor, quero que todos os campos visíveis da tabela do Espelho de Ponto sejam capturados no JSON — incluindo HR, HC, HE, HA, HH, Crédito, Débito, Saldo no Mês, Crédito Acumulado e DNC — para ter reprodução fiel da tela sem entrar manualmente no sistema.

**Why this priority**: A implementação anterior capturava apenas marcações brutas. Os campos calculados (saldo, débito, crédito acumulado) são os dados de maior interesse para avaliação de frequência e aparecem explicitamente na tabela do SIGRH.

**Independent Test**: Pode ser testado com HTML simulado contendo as colunas reais da interface; o teste confirma que o JSON gerado contém todos os campos mapeados por linha sem perder colunas presentes na tabela.

**Acceptance Scenarios**:

1. **Given** a tabela exibe colunas Data, Horários Registrados, HR, HC, HE, HA, HH, Crédito, Débito, Saldo No Mês, Crédito Acumulado e DNC, **When** o sistema extrai o espelho, **Then** cada registro diário no JSON contém um campo para cada coluna visível com o valor exibido (incluindo `---` ou `00:00` quando a célula estiver vazia).
2. **Given** uma linha mostra valores em vermelho (ausência ou débito), **When** o JSON é gerado, **Then** o valor é preservado sem distinção de cor (interpretação semântica fica com o consumidor do JSON).
3. **Given** uma linha refere-se a fim de semana ou feriado com data em vermelho, **When** o JSON é gerado, **Then** o registro diário é incluído com todos os campos disponíveis.
4. **Given** servidor com regime docente PIT não tem colunas de horas calculadas preenchidas, **When** o JSON é gerado, **Then** os campos correspondentes aparecem como `null`, não são omitidos.

---

### User Story 2 - Organizar arquivos JSON em pasta por servidor (Priority: P1)

Como operador que extrai espelhos de múltiplos servidores, quero que cada JSON seja salvo em subpasta nomeada pelo servidor, para localizar rapidamente os arquivos de uma pessoa sem filtrar por conteúdo.

**Why this priority**: Com múltiplos servidores, a pasta plana atual dificulta localização. Organização por servidor permite rastrear histórico por pessoa no sistema de arquivos.

**Independent Test**: Pode ser testado invocando extração para dois servidores distintos e verificando que os arquivos ficam em subpastas separadas, nomeadas pelo servidor, sem misturar arquivos de pessoas diferentes.

**Acceptance Scenarios**:

1. **Given** extração executada para "CELIO PROLICIANO MAIOLI", **When** o JSON é salvo, **Then** o arquivo fica em subpasta identificando o servidor (ex: `data/servidores/celio-proliciano-maioli/espelho-dezembro-2025.json`).
2. **Given** dois servidores diferentes são extraídos em sequência, **When** os JSONs são salvos, **Then** cada um está em sua própria subpasta; nenhum arquivo é sobrescrito pelo outro.
3. **Given** a subpasta do servidor não existe, **When** o JSON é salvo pela primeira vez, **Then** a subpasta é criada automaticamente sem erro.
4. **Given** JSON para mesmo servidor e período já existe, **When** nova extração é executada, **Then** o arquivo é sobrescrito pelo mais recente (um arquivo por servidor/período).

---

### User Story 3 - Preservar compatibilidade com schema anterior (Priority: P2)

Como usuário que já consome os JSONs da spec 004, quero que a nova organização não quebre os campos existentes, para não precisar ajustar scripts que dependem da estrutura atual.

**Why this priority**: Spec 004 já definiu e implementou campos como `servidor`, `periodo_referencia`, `registros`, `marcacoes`, `ocorrencias`, `observacoes`. Esses campos devem ser mantidos; os novos são adicionais.

**Independent Test**: Pode ser testado comparando o schema do JSON gerado com a lista de campos da spec 004 e verificando que todos estão presentes e inalterados.

**Acceptance Scenarios**:

1. **Given** extração executada com sucesso, **When** o JSON é inspecionado, **Then** contém todos os campos do schema atual (`run_id`, `captured_at`, `status`, `servidor`, `periodo_referencia`, `registros`, `fonte`) sem alteração de nome ou tipo.
2. **Given** JSON de um registro diário gerado, **When** inspecionado, **Then** contém campos existentes (`data`, `dia_semana`, `marcacoes`, `ocorrencias`, `observacoes`, `situacao`, `textos_visiveis`) mais os novos campos calculados quando disponíveis.

---

### Edge Cases

- O que acontece quando a tabela não exibe colunas calculadas para servidor com regime PIT docente (somente ocorrências)?
- O que acontece quando o nome do servidor contém caracteres especiais que não são válidos em nomes de pastas (barras, dois-pontos)?
- O que acontece quando dois servidores têm nomes diferentes mas que normalizam para o mesmo nome de pasta?

### Testability Requirements

- Cada user story DEVE incluir descrição de teste independente implementável antes do código de produção.
- Parsing da tabela, persistência na nova estrutura de pastas e compatibilidade retroativa DEVEM ter cenários de caminho negativo.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema DEVE capturar todos os campos visíveis de cada linha da tabela do Espelho de Ponto, incluindo HR, HC, HE, HA, HH, Crédito, Débito, Saldo No Mês, Crédito Acumulado e DNC.
- **FR-002**: O sistema DEVE salvar o JSON de cada servidor em subpasta dedicada nomeada pelo servidor, dentro do diretório de saída configurado.
- **FR-003**: O nome da subpasta DEVE ser derivado do nome normalizado do servidor (minúsculas, acentos removidos, espaços substituídos por hífen).
- **FR-004**: O sistema DEVE criar a subpasta do servidor automaticamente se não existir.
- **FR-005**: O sistema DEVE nomear o arquivo JSON pelo período de referência (ex: `espelho-dezembro-2025.json`), sobrescrevendo arquivo anterior para mesmo servidor e período.
- **FR-006**: O sistema DEVE preservar todos os campos do schema JSON atual sem remoção ou renomeação.
- **FR-007**: Novos campos calculados DEVEM estar presentes no objeto de cada registro diário; campos ausentes na página DEVEM ser `null`, não omitidos.
- **FR-008**: O sistema DEVE continuar informando o caminho do arquivo salvo ao final da execução.

### Key Entities

- **RegistroDiaPonto**: Registro de um dia no espelho. Campos existentes: `data`, `dia_semana`, `marcacoes`, `ocorrencias`, `observacoes`, `situacao`, `textos_visiveis`. Novos campos: `hr`, `hc`, `he`, `ha`, `hh`, `credito`, `debito`, `saldo_no_mes`, `credito_acumulado`, `dnc`.
- **EspelhoPontoExport**: Estrutura raiz do JSON. Campos existentes: `run_id`, `captured_at`, `status`, `servidor`, `periodo_referencia`, `registros`, `fonte`. Mantida sem alteração.
- **ServidorSelecionado**: Identificação do servidor. Campos existentes: `nome`, `identificador`, `texto_visivel`. Mantida sem alteração.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% das colunas visíveis na tabela do Espelho de Ponto aparecem como campos no JSON para o mesmo período.
- **SC-002**: Extração de cada servidor gera arquivo em subpasta própria; zero colisões de arquivo entre servidores distintos.
- **SC-003**: JSONs gerados com a nova versão contêm todos os campos presentes em JSONs gerados com a versão anterior (zero campos removidos ou renomeados).
- **SC-004**: Criação de subpasta e salvamento do arquivo completam em menos de 1 segundo após extração do HTML.

## Assumptions

- O layout da tabela do Espelho de Ponto no SIGRH mantém a ordem das colunas entre sessões.
- Servidores com regime docente PIT podem não ter colunas de horas calculadas preenchidas; nesses casos os campos são `null`.
- O diretório base de saída (`data/servidores/`) é gravável pelo processo em execução.
- A normalização de nome para pasta (ASCII, minúsculas, hífen) é suficiente para evitar conflitos no sistema operacional alvo (macOS/Linux).
- Sobrescrita silenciosa do arquivo para mesmo servidor e período é o comportamento desejado.
- Esta feature estende a spec 004; o fluxo de login, navegação, seleção de servidor e captura HTML permanecem inalterados.
