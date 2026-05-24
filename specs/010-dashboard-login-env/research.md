# Research: Proteção por Login no Dashboard

## Questão central: estático vs SSR

O dashboard atual é Astro static (output: "static"), implantado no GitHub Pages.
GitHub Pages não executa código server-side; serve apenas arquivos estáticos.

### Opção A — Verificação client-side com hash (mantém GitHub Pages)

**Como funciona**: `DASHBOARD_USER` e `DASHBOARD_PASSWORD` são lidos do ambiente
no momento do build pelo Astro. O hash do usuário e da senha (SHA-256) é embutido
no JS do bundle. No browser, o formulário de login compara o input com os hashes.
A sessão é mantida em `sessionStorage`.

- Decision: hash SHA-256 via `SubtleCrypto` (nativa no browser, sem dependência)
- Rationale: zero dependências, zero infra adicional, funciona com GitHub Pages, adequado para uso interno com acesso restrito ao URL
- Limitação: hash visível no source do bundle (mitigado por não ser o dado em cleartext; suficiente para proteção de conteúdo interno)
- Alternativa rejeitada: bcrypt no browser — depende de WASM, overhead desnecessário para este caso

### Opção B — Astro SSR com `@astrojs/node`

**Como funciona**: Adiciona adaptador Node.js ao Astro; middleware de autenticação
verifica cookie de sessão contra env vars do servidor; exige um servidor Node.js
(Railway, Fly.io, etc.).

- Rationale: proteção real server-side; hash nunca exposto ao cliente
- Alternativa rejeitada nesta versão: requer mudança de hosting (sair do GitHub Pages), adiciona complexidade de deploy e manutenção de servidor

### Decisão

**Opção A** para esta versão. Mantém GitHub Pages, zero novos serviços, adequado
para dashboard de uso interno em rede confiável. Upgrade para SSR documentado como
caminho futuro.

## Gestão de sessão

- `sessionStorage` (não `localStorage`): a sessão expira ao fechar a aba — comportamento conservador sem precisar de logout explícito
- Logout explícito limpa `sessionStorage` e redireciona para `/login`
- Redirect pós-login: URL original salvo em `sessionStorage` antes do redirect para login

## Variáveis de ambiente no Astro estático

Em Astro SSG, `import.meta.env.DASHBOARD_USER` e `import.meta.env.DASHBOARD_PASSWORD`
são substituídas em tempo de build (Vite define). Devem ser prefixadas com `PUBLIC_`
para ficarem disponíveis no JS do cliente: `PUBLIC_DASHBOARD_USER_HASH` e
`PUBLIC_DASHBOARD_PASSWORD_HASH`.

- O build Astro lê `DASHBOARD_USER` e `DASHBOARD_PASSWORD` do ambiente, calcula
  os hashes SHA-256 (em um script de build auxiliar ou via Vite plugin), e injeta
  `PUBLIC_DASHBOARD_USER_HASH` e `PUBLIC_DASHBOARD_PASSWORD_HASH` no ambiente Vite
- Alternativa mais simples: calcular o hash fora do Astro e passar diretamente
  como `PUBLIC_DASHBOARD_USER_HASH`/`PUBLIC_DASHBOARD_PASSWORD_HASH`

**Decisão**: calcular hashes fora do Astro (script auxiliar ou GitHub Actions step),
passar as variáveis `PUBLIC_*` diretamente ao build — sem plugin Vite, sem
dependência de crypto no servidor de build.

## Proteção de rotas no Astro SSG

Astro SSG não tem middleware de rotas. A proteção é feita em JavaScript client-side:
cada página verifica `sessionStorage` no `onload`; se não autenticado, redireciona
para `/login`. A página de login também verifica se já está autenticado (redireciona
para home se estiver).

## Impacto no deploy (GitHub Actions)

O workflow `deploy.yml` precisará:
1. Receber `DASHBOARD_USER` e `DASHBOARD_PASSWORD` como secrets
2. Calcular SHA-256 de cada valor (via `python3 -c` ou `sha256sum`)
3. Exportar como `PUBLIC_DASHBOARD_USER_HASH` e `PUBLIC_DASHBOARD_PASSWORD_HASH`
   antes do `npm run build`
