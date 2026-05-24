# Tasks: Proteção por Login no Dashboard

**Input**: Design documents from `specs/010-dashboard-login-env/`  
**Prerequisites**: plan.md ✓, spec.md ✓, research.md ✓, data-model.md ✓

**Tests**: MANDATORY. Testes failing antes de cada implementação conforme Constituição.

---

## Phase 1: Setup

**Purpose**: Configurações iniciais sem lógica de negócio

- [x] T001 Adicionar `DASHBOARD_USER` e `DASHBOARD_PASSWORD` ao `.env.example` na raiz do projeto
- [x] T002 [P] Adicionar `PUBLIC_DASHBOARD_USER_HASH` e `PUBLIC_DASHBOARD_PASSWORD_HASH` ao `dashboard/src/env.d.ts` (tipos ImportMeta)
- [x] T003 [P] Adicionar script `"test:e2e": "playwright test"` e dependência `"@playwright/test"` ao `dashboard/package.json`
- [x] T004 Instalar Playwright Chromium para o dashboard: `cd dashboard && npx playwright install chromium`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Módulo `auth.ts` com tipos e assinaturas — sem lógica, apenas contratos que os testes referenciam

**⚠️ CRÍTICO**: Nenhuma US pode começar sem esta fase

- [x] T005 Criar `dashboard/src/lib/auth.ts` com tipos `AuthSession` e assinaturas vazias de `checkCredentials`, `getSession`, `setSession`, `clearSession` (todas retornam `null` / `false` por enquanto)

**Checkpoint**: módulo existe, importável, testes podem compilar

---

## Phase 3: User Story 1 — Acesso Protegido ao Dashboard (P1) 🎯 MVP

**Goal**: Qualquer URL interna redireciona para `/login` se não autenticado; credenciais corretas concedem acesso.

**Independent Test**: Abrir `http://localhost:4321` sem sessão → browser deve estar em `/login`. Inserir credenciais corretas → voltar à página original.

### Testes para US1 (MANDATORY) ⚠️

> Escrever e confirmar que FALHAM antes de implementar

- [x] T006 [P] [US1] Teste unitário failing: `checkCredentials(errado, errado, hashUser, hashPass)` retorna `false` em `dashboard/src/tests/auth.test.ts`
- [x] T007 [P] [US1] Teste unitário failing: `checkCredentials(correto, correto, hashUser, hashPass)` retorna `true` em `dashboard/src/tests/auth.test.ts`
- [x] T008 [P] [US1] Teste unitário failing: `getSession()` retorna `null` quando `sessionStorage` está vazio em `dashboard/src/tests/auth.test.ts`
- [x] T009 [P] [US1] Teste unitário failing: `setSession()` persiste `{ authenticated: true }` em `sessionStorage` em `dashboard/src/tests/auth.test.ts`
- [x] T010 [P] [US1] Teste unitário failing: credenciais erradas não revelam qual campo está incorreto (mensagem genérica) em `dashboard/src/tests/auth.test.ts`
- [x] T011 [US1] Teste Playwright failing: acesso a `/` sem sessão redireciona para `/login` em `dashboard/src/tests/login.spec.ts`
- [x] T012 [US1] Teste Playwright failing: credenciais corretas → redireciona para página original em `dashboard/src/tests/login.spec.ts`
- [x] T013 [US1] Teste Playwright failing: credenciais incorretas → permanece em `/login` com mensagem de erro genérica em `dashboard/src/tests/login.spec.ts`
- [x] T014 [US1] Teste Playwright failing: `PUBLIC_DASHBOARD_USER_HASH` / `PUBLIC_DASHBOARD_PASSWORD_HASH` ausentes → login sempre falha em `dashboard/src/tests/login.spec.ts`

### Implementação de US1

- [x] T015 [US1] Implementar `checkCredentials(user, pass, userHash, passHash): Promise<boolean>` em `dashboard/src/lib/auth.ts` usando `SubtleCrypto.digest("SHA-256")` nativo do browser
- [x] T016 [US1] Implementar `getSession()`, `setSession(redirect?)` e a chave `"dashboard_auth"` no `sessionStorage` em `dashboard/src/lib/auth.ts`
- [x] T017 [US1] Criar `dashboard/src/pages/login.astro`: formulário de login com campos usuário/senha, script client-side que chama `checkCredentials`, redireciona pós-sucesso ou exibe erro genérico
- [x] T018 [US1] Adicionar guard de autenticação em `dashboard/src/pages/index.astro` (verifica `getSession()` no `<script>`, redireciona para `/login` se não autenticado)
- [x] T019 [US1] Adicionar guard de autenticação em `dashboard/src/pages/servidor/[slug].astro`
- [x] T020 [US1] Adicionar guard de autenticação em `dashboard/src/pages/servidor/[slug]/[periodo].astro`
- [x] T021 [US1] Atualizar `.github/workflows/deploy.yml`: adicionar step que calcula `PUBLIC_DASHBOARD_USER_HASH` e `PUBLIC_DASHBOARD_PASSWORD_HASH` via `python3 -c "import hashlib,os; ..."` antes do `npm run build`, lendo de `DASHBOARD_USER` e `DASHBOARD_PASSWORD` secrets

**Checkpoint**: US1 completa — dashboard protegido, login funcional, testes passando

---

## Phase 4: User Story 2 — Encerramento de Sessão (P2)

**Goal**: Botão de logout disponível em todas as páginas internas; acionar limpa sessão e redireciona para `/login`.

**Independent Test**: Após login, clicar em "Sair" → browser deve estar em `/login`; acessar URL interna diretamente → redireciona para `/login`.

### Testes para US2 (MANDATORY) ⚠️

- [x] T022 [P] [US2] Teste unitário failing: `clearSession()` remove `"dashboard_auth"` do `sessionStorage` em `dashboard/src/tests/auth.test.ts`
- [x] T023 [US2] Teste Playwright failing: botão logout clears sessão e redireciona para `/login` em `dashboard/src/tests/login.spec.ts`
- [x] T024 [US2] Teste Playwright failing: após logout, acesso direto a URL interna redireciona para `/login` em `dashboard/src/tests/login.spec.ts`

### Implementação de US2

- [x] T025 [US2] Implementar `clearSession()` em `dashboard/src/lib/auth.ts`
- [x] T026 [US2] Adicionar botão "Sair" com script de logout em `dashboard/src/pages/index.astro` e no cabeçalho/back-link de todas as páginas internas (`servidor/[slug].astro`, `servidor/[slug]/[periodo].astro`)

**Checkpoint**: US1 + US2 completas e independentemente testáveis

---

## Phase 5: Polish & Cross-Cutting Concerns

- [x] T027 [P] Adicionar estilos da tela de login ao `dashboard/public/styles/global.css` (`.login-page`, `.login-card`, `.login-form`, `.login-error`) seguindo paleta Apple-inspired existente
- [x] T028 [P] Adicionar secrets `DASHBOARD_USER` e `DASHBOARD_PASSWORD` ao README/`specs/010-dashboard-login-env/quickstart.md` — instruções de configuração no GitHub
- [x] T029 Rodar suite completa: `cd dashboard && npm test && npm run test:e2e` — todos devem passar
- [x] T030 Verificar que build estático funciona localmente com hashes reais: `PUBLIC_DASHBOARD_USER_HASH=... PUBLIC_DASHBOARD_PASSWORD_HASH=... npm run build`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Phase 1 (Setup)**: Sem dependências — iniciar imediatamente
- **Phase 2 (Foundational)**: Depende da Phase 1 — bloqueia todas as USs
- **Phase 3 (US1)**: Depende da Phase 2
- **Phase 4 (US2)**: Depende da Phase 3 (usa `clearSession` que complementa `setSession`)
- **Phase 5 (Polish)**: Depende de Phase 3 + 4

### Dentro de cada US

- Testes DEVEM falhar antes da implementação
- `auth.ts` (T015–T016) antes de `login.astro` (T017) antes dos guards (T018–T020)
- `deploy.yml` (T021) pode ser feito em paralelo com T017–T020

### Parallel Opportunities

- T006–T010 (testes unitários US1): todos em paralelo
- T018–T020 (guards das páginas): todos em paralelo após T016
- T022–T024 (testes US2): todos em paralelo
- T027–T028 (polish): em paralelo

---

## Parallel Example: US1

```bash
# Testes unitários US1 — rodar juntos:
T006: checkCredentials retorna false
T007: checkCredentials retorna true
T008: getSession retorna null
T009: setSession persiste sessão
T010: erro genérico (sem revelar campo)

# Guards — rodar juntos após T016:
T018: guard em index.astro
T019: guard em [slug].astro
T020: guard em [periodo].astro
```

---

## Implementation Strategy

### MVP (US1 apenas)

1. Phase 1: Setup
2. Phase 2: Foundational (`auth.ts` skeleton)
3. Phase 3: US1 (testes → impl → guards → deploy.yml)
4. **VALIDAR**: abrir dashboard → redirecionado para login → inserir creds → acesso
5. Merge se ok

### Entrega incremental

1. Setup + Foundational → base pronta
2. US1 → dashboard protegido (MVP!)
3. US2 → logout funcional
4. Polish → visual e docs finalizados
