# Data Model: Proteção por Login no Dashboard

## Entidades

### AuthConfig (build-time, injetado pelo Astro/Vite)

Valores calculados fora do Astro e passados como variáveis de ambiente `PUBLIC_*`.

| Campo | Tipo | Origem |
|-------|------|--------|
| `PUBLIC_DASHBOARD_USER_HASH` | `string` (hex SHA-256) | SHA-256 de `DASHBOARD_USER` calculado antes do build |
| `PUBLIC_DASHBOARD_PASSWORD_HASH` | `string` (hex SHA-256) | SHA-256 de `DASHBOARD_PASSWORD` calculado antes do build |

Ausência de qualquer uma das duas → dashboard inacessível (login sempre falha com mensagem genérica).

### AuthSession (runtime, client-side)

Armazenado em `sessionStorage` sob a chave `"dashboard_auth"`.

| Campo | Tipo | Descrição |
|-------|------|-----------|
| `authenticated` | `boolean` | `true` após login bem-sucedido |
| `redirect` | `string \| null` | URL de destino original para redirect pós-login |

Estado inicial (sem chave no sessionStorage): não autenticado.

## Transições de estado

```
NÃO AUTENTICADO
  → acessa qualquer página interna → redireciona para /login (salva redirect)
  → submete credenciais corretas  → AUTENTICADO (aplica redirect)
  → submete credenciais erradas   → NÃO AUTENTICADO (exibe erro genérico)

AUTENTICADO
  → navega entre páginas internas → permanece AUTENTICADO (sem novo login)
  → aciona logout                 → NÃO AUTENTICADO (limpa sessionStorage)
  → fecha aba/browser             → NÃO AUTENTICADO (sessionStorage é volatile)
```

## Fluxo de verificação de credenciais

```
input_user, input_password
  → SHA-256(input_user)     == PUBLIC_DASHBOARD_USER_HASH ?
  → SHA-256(input_password) == PUBLIC_DASHBOARD_PASSWORD_HASH ?
  → ambos verdadeiros → autenticado
  → qualquer falso    → erro genérico (não revela qual campo)
```

## Variáveis de ambiente (referência)

| Variável | Onde definida | Propósito |
|----------|--------------|-----------|
| `DASHBOARD_USER` | GitHub Secrets / `.env` local | Usuário em cleartext; nunca exposto ao build final |
| `DASHBOARD_PASSWORD` | GitHub Secrets / `.env` local | Senha em cleartext; nunca exposta ao build final |
| `PUBLIC_DASHBOARD_USER_HASH` | Calculada no step de build | Hash SHA-256 do usuário; embutida no bundle |
| `PUBLIC_DASHBOARD_PASSWORD_HASH` | Calculada no step de build | Hash SHA-256 da senha; embutida no bundle |
