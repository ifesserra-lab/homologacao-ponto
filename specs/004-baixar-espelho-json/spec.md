# Feature Specification: Baixar Espelho de Ponto em JSON

**Feature Branch**: `004-baixar-espelho-json`  
**Created**: 2026-05-20  
**Status**: Draft  
**Input**: User description: "apos clica em selecionar servidor baixe o Espelho de Ponto em json"

## Clarifications

### Session 2026-05-20

- Q: Qual nivel de estrutura o JSON deve ter para cada dia do espelho? -> A: Estruturar campos comuns por dia, como data, marcacoes, ocorrencias, observacoes e textos_visiveis.
- Q: Quando a exportacao em JSON deve acontecer no fluxo? -> A: Exportar automaticamente o JSON apos selecionar o servidor com sucesso.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Gerar JSON do espelho selecionado (Priority: P1)

Como usuario autenticado no SIGRH que seleciona um servidor no Espelho de Ponto, quero que os dados visiveis do espelho diario sejam baixados automaticamente em um arquivo JSON local apos a selecao, para consultar e reutilizar as informacoes sem copiar manualmente a tela.

**Why this priority**: Este e o objetivo principal solicitado e completa o fluxo iniciado por login, navegacao, busca e selecao do servidor.

**Independent Test**: Pode ser testado com uma pagina simulada de espelho diario contendo identificacao do servidor, periodo e registros de ponto; o teste confirma que o arquivo JSON contem esses dados estruturados e nao contem HTML bruto.

**Acceptance Scenarios**:

1. **Given** a pagina do espelho diario identifica o servidor selecionado e mostra registros de ponto, **When** a selecao do servidor termina com sucesso, **Then** o sistema salva automaticamente um arquivo JSON local com servidor, periodo, data de captura e registros visiveis.
2. **Given** a pagina do espelho diario esta aberta apos a selecao do servidor, **When** o JSON automatico e gerado, **Then** o sistema informa o caminho do arquivo salvo e encerra sem baixar PDF, imagem ou HTML bruto.

---

### User Story 2 - Tratar espelho vazio ou incompleto (Priority: P2)

Como usuario, quero receber uma mensagem clara quando o espelho nao possui registros ou nao pode ser interpretado com seguranca, para saber se o periodo esta vazio, se a pagina mudou ou se preciso repetir o fluxo.

**Why this priority**: O espelho pode nao conter registros para o periodo, pode exibir avisos ou pode mudar de formato. O sistema precisa evitar JSON enganoso.

**Independent Test**: Pode ser testado com paginas simuladas sem registros, com aviso institucional e com layout inesperado; cada caso deve gerar resultado claro sem inventar dados ausentes.

**Acceptance Scenarios**:

1. **Given** o espelho do servidor esta aberto mas nao ha registros de ponto no periodo, **When** o usuario solicita o JSON, **Then** o sistema salva um JSON com lista de registros vazia e mensagem de espelho sem registros.
2. **Given** a pagina aberta nao identifica claramente o servidor selecionado, **When** o usuario solicita o JSON, **Then** o sistema encerra com falha clara e nao salva dados como se fossem do servidor esperado.
3. **Given** a pagina possui registros mas alguns campos opcionais nao aparecem, **When** o JSON e gerado, **Then** o sistema preserva os registros disponiveis e marca os campos ausentes como nao informados.

---

### User Story 3 - Registrar resultado da exportacao (Priority: P3)

Como usuario, quero que cada tentativa de baixar o espelho em JSON registre sucesso ou falha, para diagnosticar problemas e rastrear qual arquivo foi gerado.

**Why this priority**: O registro local melhora auditoria e suporte, mas depende primeiro da extracao correta do espelho.

**Independent Test**: Pode ser testado executando fluxos simulados de sucesso, espelho vazio, pagina invalida e falha de escrita; o resultado deve registrar status, mensagem, servidor, periodo e caminho do arquivo quando existir.

**Acceptance Scenarios**:

1. **Given** o JSON do espelho foi salvo, **When** a execucao termina, **Then** o resultado local registra sucesso, servidor, periodo e caminho do arquivo do espelho.
2. **Given** a exportacao falha por pagina invalida, sessao expirada, bloqueio anti-automacao ou falha de escrita, **When** a execucao termina, **Then** o resultado local registra falha, motivo e etapa onde parou.

### Edge Cases

- O espelho mostra apenas avisos e nenhuma linha de ponto; o JSON deve diferenciar "sem registros" de falha de leitura.
- O periodo exibido na pagina difere do periodo esperado; o sistema deve registrar o periodo visivel e alertar quando houver divergencia detectavel.
- A tela exibe dias com multiplas marcacoes, justificativas, saldos, ferias, ocorrencias ou observacoes; o JSON deve preservar os textos visiveis por dia sem interpretar valores ambiguos como calculos oficiais.
- A pagina contem dados do servidor errado ou nao identifica servidor; o sistema deve falhar sem persistir registros como se fossem do servidor solicitado.
- A sessao expira apos a selecao do servidor e antes da exportacao; o sistema deve parar sem tentar reautenticacao automatica.
- O SIGRH apresenta CAPTCHA, MFA ou bloqueio anti-automacao; o sistema deve abortar e informar que a protecao impede automacao.
- O arquivo JSON de destino nao pode ser escrito; o sistema deve informar falha sem declarar sucesso.

### Testability Requirements

- Cada historia de usuario deve ter teste automatizado criado antes da implementacao.
- O fluxo de exportacao deve ter testes positivos para espelho com registros e espelho vazio, e testes negativos para pagina invalida, servidor divergente, sessao expirada, bloqueio anti-automacao e falha de escrita.
- Os testes devem validar comportamento observavel pelo usuario, incluindo status final, mensagem, caminho do JSON e dados estruturados gerados.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST baixar automaticamente em JSON os dados visiveis do Espelho de Ponto apos selecionar um servidor com sucesso.
- **FR-002**: O sistema MUST confirmar que a pagina do espelho identifica o servidor selecionado antes de extrair registros.
- **FR-003**: O JSON do espelho MUST conter, quando visiveis, servidor, identificador do servidor, periodo de referencia, data/hora de captura, registros por dia e mensagens/avisos da pagina.
- **FR-004**: O sistema MUST salvar o JSON do espelho em arquivo local por execucao e informar o caminho ao usuario.
- **FR-005**: O sistema MUST diferenciar espelho sem registros de falha de leitura da pagina.
- **FR-006**: O sistema MUST estruturar cada dia com campos comuns quando visiveis, incluindo data, marcacoes, ocorrencias, observacoes e textos_visiveis, sem inventar campos ausentes.
- **FR-007**: O sistema MUST encerrar com mensagem clara quando a pagina aberta nao for o espelho do servidor selecionado.
- **FR-008**: O sistema MUST preservar a regra de nao tentar reautenticacao automatica quando a sessao expirar durante a exportacao.
- **FR-009**: O sistema MUST abortar a execucao quando detectar CAPTCHA, MFA ou bloqueio anti-automacao, informando que a protecao impede automacao.
- **FR-010**: O sistema MUST registrar o resultado da tentativa com status, servidor, periodo quando houver, mensagem, caminho do JSON quando houver e data/hora da conclusao.
- **FR-011**: O sistema MUST evitar persistir HTML bruto, screenshots, cookies, senhas ou tokens por padrao.
- **FR-012**: O sistema MUST tratar falha de escrita do JSON local como execucao malsucedida com mensagem clara ao usuario.

### Key Entities

- **EspelhoPontoExport**: Arquivo JSON gerado para um espelho de ponto; contem metadados do servidor, periodo, captura, registros e avisos visiveis.
- **RegistroDiaPonto**: Dados visiveis de um dia no espelho; contem campos comuns quando disponiveis, como data, dia da semana, marcacoes, ocorrencias, observacoes, situacao e textos_visiveis para preservar conteudo que nao se encaixa nos campos estruturados.
- **ServidorSelecionado**: Servidor cujo espelho esta aberto; inclui nome visivel e identificador quando disponivel.
- **ExportacaoEspelhoResult**: Resultado local da tentativa de exportacao; inclui status, servidor, periodo, caminho do JSON, mensagem e data/hora.
- **AuthenticatedUserSession**: Sessao autenticada existente usada para acessar e exportar o espelho dentro das permissoes do usuario.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em ambiente de teste controlado com espelho valido, 95% das execucoes geram automaticamente um JSON local em ate 30 segundos apos a selecao bem-sucedida do servidor.
- **SC-002**: 100% dos testes de pagina invalida ou servidor divergente terminam sem gerar registros associados ao servidor errado.
- **SC-003**: 100% dos JSONs gerados incluem servidor, data/hora de captura, status da exportacao e lista de registros, mesmo quando a lista estiver vazia.
- **SC-004**: 100% dos fluxos de falha apresentam mensagem final compreensivel e registram a etapa onde a exportacao parou.
- **SC-005**: 100% das execucoes evitam persistir HTML bruto, cookies, senhas, tokens, screenshots ou traces por padrao.

## Assumptions

- O login, a navegacao ate o Espelho de Ponto, a busca e a selecao do servidor ja estao disponiveis em features anteriores.
- O objetivo desta feature e exportar dados visiveis do espelho em JSON; baixar PDF, imagem, planilha ou interpretar/calcular saldos oficiais fica fora do escopo.
- Quando o layout do SIGRH apresentar campos opcionais diferentes entre dias, o JSON deve preservar o que estiver visivel e deixar ausencias explicitas.
- As regras de seguranca existentes continuam validas: nao contornar CAPTCHA/MFA, nao persistir credenciais por padrao e nao salvar artefatos sensiveis sem consentimento explicito.
