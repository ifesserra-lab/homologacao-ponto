# Feature Specification: Selecionar Servidor no Espelho de Ponto

**Feature Branch**: `003-selecionar-servidor`  
**Created**: 2026-05-20  
**Status**: Draft  
**Input**: User description: "clique no botão de \"Selecionar Servidor\""

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Abrir espelho do servidor encontrado (Priority: P1)

Como usuario autenticado no SIGRH, quero selecionar o servidor retornado pela consulta do Espelho de Ponto, para abrir a pagina de ponto diario daquele servidor sem precisar clicar manualmente no resultado.

**Why this priority**: Este e o passo imediatamente posterior a busca do servidor e desbloqueia a visualizacao do espelho individual.

**Independent Test**: Pode ser testado com uma tela simulada de resultados contendo exatamente um servidor esperado e um controle "Selecionar Servidor"; o teste confirma que a selecao abre uma pagina com o nome ou identificador do servidor selecionado.

**Acceptance Scenarios**:

1. **Given** a tela de resultados do Espelho de Ponto mostra o servidor esperado com o controle "Selecionar Servidor", **When** o usuario solicita a selecao do servidor, **Then** o sistema aciona o controle correto e confirma a pagina de ponto diario do servidor selecionado.
2. **Given** a tela de resultados mostra exatamente um servidor compativel com a busca, **When** o sistema seleciona o servidor, **Then** a selecao usa esse unico resultado e nao escolhe menus ou links fora da listagem.

---

### User Story 2 - Informar quando o servidor nao pode ser selecionado (Priority: P2)

Como usuario, quero receber uma mensagem clara quando o resultado de busca nao permite selecionar o servidor, para saber se preciso ajustar o nome pesquisado, permissoes ou repetir a consulta.

**Why this priority**: A consulta pode retornar nenhum servidor, multiplos servidores ou uma listagem sem o botao esperado. Sem diagnostico, o usuario nao sabe qual acao corrigir.

**Independent Test**: Pode ser testado com telas simuladas sem resultados, com multiplos resultados ambiguos e com resultado sem controle de selecao; cada caso deve parar com mensagem clara e sem clicar no servidor errado.

**Acceptance Scenarios**:

1. **Given** a tela de resultados nao contem servidor compativel, **When** o usuario solicita selecao, **Then** o sistema encerra com mensagem de servidor nao encontrado.
2. **Given** a tela de resultados contem multiplos servidores compativeis sem criterio unico, **When** o usuario solicita selecao, **Then** o sistema encerra com mensagem de resultado ambiguo e nao seleciona nenhum servidor.
3. **Given** o servidor aparece na listagem mas o controle "Selecionar Servidor" nao esta disponivel, **When** o usuario solicita selecao, **Then** o sistema informa que a selecao nao esta disponivel para aquele resultado.

---

### User Story 3 - Registrar resultado da selecao (Priority: P3)

Como usuario, quero que a execucao registre se a selecao abriu o espelho individual ou onde falhou, para diagnosticar problemas em execucoes futuras.

**Why this priority**: O registro local mantem o fluxo auditavel e segue o padrao ja usado para login, navegacao e consulta.

**Independent Test**: Pode ser testado executando selecoes simuladas de sucesso e falha e verificando que o resultado local contem status, servidor solicitado, servidor selecionado quando houver, mensagem e data/hora da tentativa.

**Acceptance Scenarios**:

1. **Given** a selecao abriu o espelho diario do servidor, **When** a execucao termina, **Then** o resultado local registra sucesso, servidor selecionado e data/hora da conclusao.
2. **Given** a selecao falhou por resultado ausente, ambiguo, sessao expirada ou controle indisponivel, **When** a execucao termina, **Then** o resultado local registra falha, motivo e etapa onde parou.

### Edge Cases

- A listagem mostra um servidor com acentos, maiusculas ou matricula junto ao nome; o sistema deve reconhecer equivalencias claras sem confundir servidores diferentes.
- A busca retorna mais de um servidor com nomes parecidos; o sistema deve evitar selecao automatica ambigua.
- O controle de selecao aparece como icone, link sem texto ou titulo "Selecionar Servidor"; o sistema deve reconhecer o controle quando ele estiver associado ao resultado correto.
- A sessao expira depois da busca e antes da selecao; o sistema deve parar sem tentar reautenticacao automatica.
- O SIGRH exibe aviso apos a selecao antes do espelho individual; o sistema deve considerar sucesso apenas se a pagina final identificar o servidor selecionado.
- O SIGRH apresenta CAPTCHA, MFA ou bloqueio anti-automacao; o sistema deve abortar e informar que a protecao impede automacao.

### Testability Requirements

- Cada historia de usuario deve ter teste automatizado criado antes da implementacao.
- O fluxo de selecao deve ter testes positivos para resultado unico e testes negativos para resultado ausente, resultado ambiguo, sessao expirada, bloqueio anti-automacao e controle de selecao indisponivel.
- Os testes devem validar comportamento observavel pelo usuario, incluindo status final, mensagem e servidor selecionado quando houver.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: O sistema MUST permitir que um usuario solicite a selecao de um servidor exibido na listagem de resultados do Espelho de Ponto.
- **FR-002**: O sistema MUST selecionar apenas o controle "Selecionar Servidor" associado ao resultado do servidor esperado.
- **FR-003**: O sistema MUST confirmar sucesso somente quando a pagina final identificar o servidor selecionado no espelho diario.
- **FR-004**: O sistema MUST encerrar com mensagem clara quando nenhum servidor compativel for encontrado.
- **FR-005**: O sistema MUST encerrar sem selecionar servidor quando houver multiplos resultados compativeis sem criterio unico.
- **FR-006**: O sistema MUST informar quando o resultado existe mas o controle de selecao nao esta disponivel.
- **FR-007**: O sistema MUST preservar a regra de nao tentar reautenticacao automatica quando a sessao expirar durante a selecao.
- **FR-008**: O sistema MUST tratar variacoes obvias de acentuacao, capitalizacao e espacamento do nome do servidor como equivalentes.
- **FR-009**: O sistema MUST abortar a execucao quando detectar CAPTCHA, MFA ou bloqueio anti-automacao, informando que a protecao impede automacao.
- **FR-010**: O sistema MUST registrar o resultado da tentativa com status, servidor solicitado, servidor selecionado quando houver, mensagem e data/hora da conclusao.
- **FR-011**: O sistema MUST manter a selecao dentro do fluxo do Espelho de Ponto, sem clicar em menus, atalhos ou links globais que contenham texto parecido.
- **FR-012**: O sistema MUST tratar falha de escrita do resultado local como execucao malsucedida com mensagem clara ao usuario.

### Key Entities

- **ServidorConsulta**: Servidor procurado pelo usuario na listagem do Espelho de Ponto; inclui nome solicitado e identificador visivel quando disponivel.
- **ServidorResultado**: Resultado exibido na listagem com nome, identificador, disponibilidade do controle de selecao e grau de correspondencia com a busca.
- **SelecaoServidorResult**: Resultado local da tentativa de selecao; inclui status, servidor solicitado, servidor selecionado, etapa final, mensagem e data/hora.
- **AuthenticatedUserSession**: Sessao autenticada existente usada para interagir com o SIGRH dentro das permissoes do usuario.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Em ambiente de teste controlado com resultado unico disponivel, 95% das execucoes abrem o espelho diario do servidor sem intervencao manual.
- **SC-002**: 100% dos testes com resultados ausentes, ambiguos ou sem controle de selecao terminam sem escolher servidor incorreto.
- **SC-003**: Usuarios recebem uma mensagem final compreensivel em ate 30 segundos para fluxos de sucesso ou falha apos a listagem estar visivel.
- **SC-004**: 100% das execucoes bem-sucedidas confirmam o nome ou identificador do servidor selecionado na pagina final.
- **SC-005**: 100% das execucoes persistem resultado local com status, servidor solicitado, mensagem e data/hora de conclusao para auditoria local.

## Assumptions

- O login, a navegacao ate o Espelho de Ponto e a busca inicial do servidor ja estao disponiveis em fluxos anteriores ou serao reutilizados por esta feature.
- O resultado de sucesso esperado e abrir a pagina de ponto diario do servidor selecionado; extrair, baixar ou interpretar os registros do ponto continua fora do escopo.
- Quando houver exatamente um resultado claramente compativel com a busca, ele pode ser selecionado automaticamente.
- As regras de seguranca existentes continuam validas: nao contornar CAPTCHA/MFA, nao persistir credenciais por padrao e nao salvar artefatos sensiveis sem consentimento explicito.
