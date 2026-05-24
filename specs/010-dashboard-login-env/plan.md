# Implementation Plan: Proteção por Login no Dashboard

**Branch**: `010-dashboard-login-env` | **Date**: 2026-05-24 | **Spec**: [spec.md](spec.md)  
**Input**: Feature specification from `specs/010-dashboard-login-env/spec.md`

## Summary

Adicionar proteção por login ao dashboard Astro estático. Credenciais (`DASHBOARD_USER`,
`DASHBOARD_PASSWORD`) são definidas via variáveis de ambiente e seus hashes SHA-256
são embutidos no bundle em tempo de build. O browser verifica as credenciais contra
os hashes usando a Web Crypto API nativa (sem dependências extras). Sessão mantida
em `sessionStorage`. Cada página interna verifica autenticação no carregamento e
redireciona para `/login` se não autenticado.

## Technical Context

**Language/Version**: TypeScript (dashboard Astro) — exceção de constituição registrada abaixo  
**Primary Dependencies**: Astro (existente), Web Crypto API nativa (browser), `SubtleCrypto.digest` (sem nova dependência)  
**Storage**: `sessionStorage` (client-side, volátil por aba)  
**Testing**: vitest (lógica auth.ts) + Playwright (fluxo E2E login)  
**Target Platform**: Browser (Chrome, Firefox, Safari modernos); build no GitHub Actions  
**Project Type**: Web application — dashboard frontend estático  
**Performance Goals**: Verificação de hash < 50ms; tela de login renderiza < 1s  
**Constraints**: Manter compatibilidade com GitHub Pages (sem SSR); zero novas dependências npm  
**Scale/Scope**: Uso interno; 1 par de credenciais; 1–10 usuários simultâneos

## Constitution Check

### Princípio I — Test-First Delivery ✅

- US1 (acesso protegido): primeiro teste failing → `auth.test.ts`: `checkCredentials(wrongUser, wrongPass, hash, hash)` retorna `false`
- US1: segundo teste → Playwright: acesso a `/` sem sessão redireciona para `/login`
- US2 (logout): primeiro teste failing → `auth.test.ts`: `clearSession()` remove chave do sessionStorage
- Todos os testes precedem implementação nas tasks

### Princípio II — Python como linguagem ⚠️ EXCEÇÃO

**Violação registrada**: dashboard é TypeScript/Astro (estabelecido na feature 008).  
**Justificativa**: browser requer JavaScript; Astro é o framework do dashboard já adotado.  
**Alternativa rejeitada**: reescrever dashboard em Python — não existe runtime Python no browser.  
**Mitigação**: Python é usado no step de build para calcular os hashes SHA-256 antes do `npm run build`.

### Princípio III — Object-Oriented Domain Design ✅

- `AuthService` (módulo `auth.ts`): encapsula `checkCredentials()`, `getSession()`, `setSession()`, `clearSession()`
- Responsabilidade única: verificação de credenciais separada de gestão de sessão

### Princípio IV — Intentional Design Patterns ✅

- **Guard pattern** (checagem de sessão em cada página): reduz duplicação de lógica de redirect
- **Module/Service pattern** (`auth.ts`): isola crypto e sessionStorage do markup das páginas

### Princípio V — Verifiable Quality Gates ✅

```bash
# Testes unitários (vitest)
cd dashboard && npm test

# Testes E2E (Playwright — fluxo de login)
cd dashboard && npm run test:e2e

# Validação independente US1: sem sessão → redireciona para /login
# Validação independente US2: logout → limpa sessão → redirect
```

## Project Structure

### Documentation (this feature)

```text
specs/010-dashboard-login-env/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
└── tasks.md  ← gerado por /speckit-tasks
```

### Source Code (dashboard)

```text
dashboard/
├── src/
│   ├── lib/
│   │   └── auth.ts                 # AuthService: hash check + session management
│   ├── pages/
│   │   ├── login.astro             # tela de login (formulário + lógica client)
│   │   ├── index.astro             # guard adicionado
│   │   └── servidor/
│   │       ├── [slug].astro        # guard adicionado
│   │       └── [slug]/
│   │           └── [periodo].astro # guard adicionado
│   └── tests/
│       ├── auth.test.ts            # vitest: AuthService
│       └── login.spec.ts           # Playwright E2E: fluxo completo
├── .env.example                    # adiciona DASHBOARD_USER / DASHBOARD_PASSWORD
└── package.json                    # adiciona script test:e2e

.github/workflows/
└── deploy.yml                      # adiciona step: calcular hashes + exportar PUBLIC_*

.env.example                        # (raiz) adiciona DASHBOARD_USER / DASHBOARD_PASSWORD
```

## Complexity Tracking

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| TypeScript/Astro em vez de Python | Browser requer JS; dashboard já é Astro (feature 008) | Python não executa no browser |
