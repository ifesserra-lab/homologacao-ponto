# Feature Specification: Navegacao ate Espelho do Ponto

**Feature Branch**: `002-navegar-espelho-ponto`  
**Created**: 2026-05-20  
**Status**: Draft  
**Input**: User description: "apos logar clique em Chefia de Unidade, depois homologação de Ponto Eletronico, depois relatorio e depois em espelho do ponto"

## Clarifications

### Session 2026-05-20

- Q: O que deve acontecer depois do clique em "Espelho do Ponto"? → A: Parar quando abrir a tela Espelho do Ponto.
- Q: Como confirmar que a tela "Espelho do Ponto" foi aberta? → A: Confirmar por titulo, cabecalho ou breadcrumb visivel "Espelho do Ponto".
- Q: Quanto tempo aguardar por cada menu ou submenu antes de declarar falha? → A: Aguardar ate 15 segundos por etapa.
- Q: Onde registrar o resultado da navegacao ate "Espelho do Ponto"? → A: Salvar resultado em JSON local por execucao.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Acessar espelho do ponto apos login (Priority: P1)

Como usuario autenticado no SIGRH com perfil autorizado de chefia, quero que o sistema navegue pelo caminho de menu "Chefia de Unidade" -> "Homologacao de Ponto Eletronico" -> "Relatorio" -> "Espelho do Ponto", para chegar diretamente a tela de relatorio de espelho do ponto sem navegacao manual repetitiva.

**Why this priority**: Este e o caminho essencial solicitado e desbloqueia a consulta do espelho do ponto, que e o objetivo imediato do fluxo apos login.

**Independent Test**: Pode ser testado com uma sessao autenticada simulada contendo os itens de menu esperados; o teste confirma que o sistema encontra titulo, cabecalho ou breadcrumb visivel "Espelho do Ponto" e declara a navegacao concluida.

**Acceptance Scenarios**:

1. **Given** uma sessao autenticada com perfil que possui o menu "Chefia de Unidade", **When** o usuario solicita o acesso ao espelho do ponto, **Then** o sistema percorre a sequencia de menus solicitada e confirma chegada a tela por titulo, cabecalho ou breadcrumb visivel "Espelho do Ponto".
2. **Given** uma sessao autenticada ja posicionada em outra area do SIGRH, **When** o usuario solicita o acesso ao espelho do ponto, **Then** o sistema inicia a navegacao a partir da tela atual sem exigir novo login quando a sessao ainda estiver valida.

---

### User Story 2 - Informar bloqueios de permissao ou menu ausente (Priority: P2)

Como usuario autenticado, quero receber uma mensagem clara quando meu perfil nao possuir algum item do caminho de chefia, para entender se o impedimento e permissao, sessao expirada ou mudanca no SIGRH.

**Why this priority**: O fluxo depende de menus que podem variar por perfil. Uma falha silenciosa deixaria o usuario sem saber se precisa de permissao, nova autenticacao ou ajuste no sistema.

**Independent Test**: Pode ser testado removendo cada item do caminho em paginas simuladas e validando que o sistema para no ponto correto, informa o item ausente e nao tenta acessar areas fora do escopo.

**Acceptance Scenarios**:

1. **Given** uma sessao autenticada sem acesso a "Chefia de Unidade", **When** o usuario solicita o espelho do ponto, **Then** o sistema encerra a navegacao com mensagem de permissao ou menu indisponivel.
2. **Given** uma sessao autenticada com "Chefia de Unidade", mas sem "Homologacao de Ponto Eletronico", **When** o usuario solicita o espelho do ponto, **Then** o sistema informa exatamente qual etapa do caminho nao foi encontrada.
3. **Given** uma sessao expirada durante a navegacao, **When** o sistema detectar retorno para tela de login ou perda de autenticacao, **Then** a navegacao e encerrada com mensagem de sessao expirada e sem nova autenticacao automatica.

---

### User Story 3 - Registrar resultado da navegacao (Priority: P3)

Como usuario, quero que a execucao registre se chegou ao espelho do ponto ou onde falhou, para que eu possa diagnosticar problemas e usar esse resultado em coletas posteriores.

**Why this priority**: O registro do resultado melhora suporte e repetibilidade, mas o valor principal continua sendo chegar a tela correta.

**Independent Test**: Pode ser testado executando fluxos de sucesso e falha com paginas simuladas e verificando que o arquivo JSON local da execucao contem status, etapa final, mensagem e data/hora da tentativa.

**Acceptance Scenarios**:

1. **Given** que a navegacao chegou ao espelho do ponto, **When** a execucao terminar, **Then** o arquivo JSON local registra status de sucesso, etapa "Espelho do Ponto" e data/hora da conclusao.
2. **Given** que a navegacao parou por menu ausente, permissao insuficiente ou sessao expirada, **When** a execucao terminar, **Then** o arquivo JSON local registra status de falha, etapa onde parou e mensagem compreensivel ao usuario.

### Edge Cases

- O item de menu existe, mas usa acentuacao ou variacao visual diferente de "Homologacao de Ponto Eletronico"; o sistema deve reconhecer equivalentes claros sem escolher menus de outro assunto.
- O menu ou submenu demora a aparecer; o sistema deve aguardar ate 15 segundos por etapa antes de declarar falha.
- O usuario autenticado nao possui perfil de chefia; o sistema deve informar falta de permissao ou menu indisponivel sem considerar isso erro de credenciais.
- A sessao expira apos o login e antes da tela "Espelho do Ponto"; o sistema deve parar sem tentar reautenticacao automatica.
- O SIGRH exibe aviso, mensagem intermediaria ou redirecionamento antes do relatorio; o sistema deve continuar apenas se o destino ainda for claramente o fluxo de espelho do ponto.
- O SIGRH apresenta CAPTCHA, MFA ou bloqueio anti-automacao; o sistema deve abortar e informar que a protecao impede automacao.

### Testability Requirements

- Cada historia de usuario deve ter teste automatizado criado antes da implementacao.
- O fluxo de navegacao deve ter testes positivos para a sequencia completa e testes negativos para menu ausente, permissao insuficiente, sessao expirada e protecao anti-automacao.
- Os testes devem validar o comportamento observavel pelo usuario, incluindo status final, mensagem e etapa onde o fluxo parou.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST permitir que um usuario ja autenticado solicite a navegacao ate a tela "Espelho do Ponto".
- **FR-002**: O sistema MUST seguir a ordem de navegacao "Chefia de Unidade", "Homologacao de Ponto Eletronico", "Relatorio" e "Espelho do Ponto".
- **FR-003**: O sistema MUST confirmar sucesso somente quando a tela final exibir titulo, cabecalho ou breadcrumb visivel "Espelho do Ponto".
- **FR-004**: O sistema MUST encerrar a navegacao com mensagem clara quando qualquer item obrigatorio do caminho nao estiver disponivel.
- **FR-005**: O sistema MUST indicar em qual etapa a navegacao parou quando ocorrer falha por menu ausente, permissao insuficiente, sessao expirada ou destino inesperado.
- **FR-006**: O sistema MUST preservar a regra de nao tentar reautenticacao automatica quando a sessao expirar durante a navegacao.
- **FR-007**: O sistema MUST restringir esta funcionalidade ao caminho do relatorio "Espelho do Ponto" dentro de "Homologacao de Ponto Eletronico", sem navegar para outros relatorios ou areas administrativas.
- **FR-008**: O sistema MUST tratar variacoes obvias de acentuacao e capitalizacao dos rotulos do menu como equivalentes ao caminho solicitado.
- **FR-009**: O sistema MUST abortar a execucao quando detectar CAPTCHA, MFA ou bloqueio anti-automacao, informando que a protecao impede automacao.
- **FR-010**: O sistema MUST registrar o resultado da tentativa com status, etapa final alcancada, mensagem de sucesso ou falha e data/hora da conclusao.
- **FR-011**: O sistema MUST manter a navegacao dentro dos limites ja definidos para interacoes com o SIGRH, incluindo ritmo conservador entre acoes e limite de paginas por execucao.
- **FR-012**: O sistema MUST encerrar esta funcionalidade ao abrir a tela "Espelho do Ponto"; gerar, filtrar, baixar ou extrair o conteudo do relatorio fica fora deste escopo.
- **FR-013**: O sistema MUST aguardar ate 15 segundos por cada etapa do caminho de menu antes de declarar falha por item indisponivel ou carregamento excedido.
- **FR-014**: O sistema MUST salvar o resultado da navegacao em um arquivo JSON local por execucao, contendo status, etapa final alcancada, mensagem, data/hora da conclusao e indicador de sucesso ou falha.
- **FR-015**: O sistema MUST tratar falha de escrita do JSON local como execucao malsucedida com mensagem clara ao usuario.

### Key Entities

- **NavigationPath**: Sequencia esperada de etapas de menu para chegar ao espelho do ponto; inclui os rotulos "Chefia de Unidade", "Homologacao de Ponto Eletronico", "Relatorio" e "Espelho do Ponto".
- **NavigationStep**: Uma etapa individual do caminho, com nome esperado, estado encontrado/nao encontrado e mensagem associada quando houver falha.
- **NavigationResult**: Resultado da tentativa de navegacao salvo em JSON local por execucao, contendo status, etapa final alcancada, mensagem, data/hora da conclusao e indicacao de sucesso ou falha.
- **AuthenticatedUserSession**: Sessao de usuario ja autenticada e autorizada a navegar no SIGRH dentro das permissoes do usuario.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em ambiente de teste controlado com menus esperados disponiveis, 95% das execucoes chegam a tela "Espelho do Ponto" sem intervencao manual.
- **SC-002**: 100% dos testes de menu ausente ou permissao insuficiente identificam a etapa onde a navegacao parou.
- **SC-003**: Usuarios recebem uma mensagem final compreensivel em ate 60 segundos para fluxos de sucesso ou falha, respeitando o limite de ate 15 segundos por etapa.
- **SC-004**: 100% das execucoes permanecem restritas ao caminho solicitado e nao acessam outros relatorios fora de "Espelho do Ponto".
- **SC-005**: 100% das execucoes persistem JSON local com status, etapa final e data/hora de conclusao para auditoria local da tentativa.

## Assumptions

- O login e a manutencao da sessao autenticada ja foram tratados pela feature anterior de login SIGRH.
- O usuario alvo possui credenciais validas e, para o fluxo de sucesso, perfil com acesso a "Chefia de Unidade".
- O objetivo desta feature e chegar a tela do relatorio "Espelho do Ponto" e parar nesse ponto; extrair, filtrar, gerar ou baixar o conteudo detalhado do relatorio pode ser especificado em feature posterior.
- Variacoes simples de acentuacao, capitalizacao e espacos nos rotulos do SIGRH devem ser aceitas, desde que continuem representando claramente os mesmos itens de menu.
- As regras de seguranca existentes continuam validas: nao contornar CAPTCHA/MFA, nao persistir credenciais por padrao e nao salvar artefatos sensiveis sem consentimento explicito.
