# Feature Specification: Proteção por Login no Dashboard

**Feature Branch**: `010-dashboard-login-env`  
**Created**: 2026-05-24  
**Status**: Draft  
**Input**: User description: "adicione uma tela de login no qual a senha e o usuário fica na env."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Acesso protegido ao dashboard (Priority: P1)

Um gestor acessa a URL do dashboard e, antes de ver qualquer dado de ponto, é apresentado a uma tela de login. Ele insere o usuário e a senha configurados na variável de ambiente e, ao acertar, acessa o conteúdo normalmente. Quem não tiver as credenciais vê apenas a tela de login.

**Why this priority**: Sem proteção, os dados de frequência dos servidores ficam públicos para qualquer pessoa que conheça a URL.

**Independent Test**: Pode ser testado acessando o dashboard sem credenciais (deve exibir o formulário de login) e depois fornecendo as credenciais corretas (deve exibir a lista de servidores).

**Acceptance Scenarios**:

1. **Given** visitante não autenticado acessa qualquer página do dashboard, **When** a página é carregada, **Then** é redirecionado para a tela de login antes de ver qualquer conteúdo.
2. **Given** usuário está na tela de login, **When** insere usuário e senha correspondentes aos valores definidos nas variáveis de ambiente e confirma, **Then** é redirecionado para a página que tentou acessar originalmente e vê o conteúdo.
3. **Given** usuário está na tela de login, **When** insere credenciais incorretas, **Then** permanece na tela de login com mensagem de erro genérica (sem revelar qual campo está errado).

---

### User Story 2 - Encerramento de sessão (Priority: P2)

O gestor autenticado pode encerrar a sessão manualmente. Após o logout, qualquer tentativa de acessar o dashboard redireciona novamente para o login.

**Why this priority**: Permite uso seguro em dispositivos compartilhados.

**Independent Test**: Após login bem-sucedido, acionar logout deve retornar à tela de login e impedir acesso direto às páginas internas.

**Acceptance Scenarios**:

1. **Given** usuário autenticado, **When** aciona o botão de logout, **Then** a sessão é encerrada e o usuário é redirecionado para a tela de login.
2. **Given** sessão encerrada, **When** usuário tenta acessar URL direta de uma página interna, **Then** é redirecionado para a tela de login.

---

### Edge Cases

- O que acontece se as variáveis de ambiente de credenciais não estiverem definidas? O acesso ao dashboard deve ser bloqueado completamente (sem fallback de acesso aberto).
- O que acontece com múltiplos erros de login em sequência? Mensagem genérica a cada tentativa; rate-limit fora do escopo desta versão.
- Sessão expira após inatividade? Sessão persiste enquanto o browser mantiver o estado; prazo de expiração não definido nesta versão.

### Testability Requirements

- Cada cenário de aceite DEVE ser testável de forma independente via navegação no browser.
- Fluxos de erro (credenciais erradas, env não configurada) DEVEM ter cenários negativos explícitos.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: Sistema DEVE exibir tela de login para qualquer visitante não autenticado que acesse o dashboard.
- **FR-002**: Sistema DEVE verificar as credenciais informadas contra os valores definidos em variáveis de ambiente (`DASHBOARD_USER` e `DASHBOARD_PASSWORD`).
- **FR-003**: Sistema DEVE conceder acesso ao conteúdo do dashboard somente após autenticação bem-sucedida.
- **FR-004**: Sistema DEVE manter a sessão do usuário autenticado entre navegações internas sem solicitar login novamente.
- **FR-005**: Sistema DEVE permitir que o usuário encerre a sessão explicitamente via botão de logout.
- **FR-006**: Sistema DEVE exibir mensagem de erro genérica em caso de credenciais incorretas, sem revelar qual campo está errado.
- **FR-007**: Sistema DEVE bloquear todo acesso ao dashboard quando as variáveis de ambiente de credenciais não estiverem definidas.
- **FR-008**: Sistema DEVE redirecionar o usuário para a página de destino original após login bem-sucedido.

### Key Entities

- **Credenciais de ambiente**: par usuário/senha definido nas variáveis de ambiente que configuram o acesso ao dashboard; não armazenado no código-fonte nem no repositório.
- **Sessão autenticada**: estado que indica que o usuário forneceu credenciais válidas; persiste enquanto o browser mantiver o contexto de sessão.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: 100% das URLs do dashboard retornam a tela de login para visitantes não autenticados.
- **SC-002**: O processo de login (inserir credenciais + confirmar) é concluído em menos de 5 segundos em condições normais.
- **SC-003**: Credenciais incorretas nunca revelam qual campo (usuário ou senha) está errado em nenhuma das tentativas.
- **SC-004**: Nenhum dado de ponto dos servidores é acessível sem autenticação prévia em 100% das rotas.

## Assumptions

- As credenciais são únicas (um único par usuário/senha) — múltiplos usuários com permissões distintas estão fora do escopo desta versão.
- A proteção é aplicada apenas ao dashboard; o scraper e os JSONs em `data/` não fazem parte do escopo.
- Suporte a múltiplos browsers simultâneos com o mesmo usuário é permitido.
- Não há requisito de auditoria de acesso (log de logins) nesta versão.
- A tela de login segue o mesmo estilo visual do dashboard existente.
