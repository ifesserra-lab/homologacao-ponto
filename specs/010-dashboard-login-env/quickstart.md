# Quickstart: Proteção por Login no Dashboard

## Configuração local

1. Adicione ao `.env` na raiz do projeto:
   ```
   DASHBOARD_USER=seu_usuario
   DASHBOARD_PASSWORD=sua_senha_segura
   ```

2. Calcule os hashes e configure o ambiente do Astro:
   ```bash
   export PUBLIC_DASHBOARD_USER_HASH=$(python3 -c "import hashlib,os; print(hashlib.sha256(os.environ['DASHBOARD_USER'].encode()).hexdigest())")
   export PUBLIC_DASHBOARD_PASSWORD_HASH=$(python3 -c "import hashlib,os; print(hashlib.sha256(os.environ['DASHBOARD_PASSWORD'].encode()).hexdigest())")
   ```

3. Suba o dashboard:
   ```bash
   make dashboard
   # ou: cd dashboard && npm run dev
   ```

4. Acesse `http://localhost:4321` — será redirecionado para `/login`.

## Configuração no GitHub Actions

Adicione dois novos secrets em Settings → Secrets → Actions:
- `DASHBOARD_USER`
- `DASHBOARD_PASSWORD`

O workflow `deploy.yml` calculará os hashes automaticamente antes do build.

## Rodar testes

```bash
# Testes do dashboard (vitest)
cd dashboard && npm test

# Testes Playwright (login flow)
cd dashboard && npm run test:e2e
```

## Estrutura relevante

```text
dashboard/
├── src/
│   ├── lib/
│   │   └── auth.ts            # lógica de verificação e sessão
│   └── pages/
│       ├── login.astro        # página de login
│       ├── index.astro        # guard: redireciona se não autenticado
│       └── servidor/          # guard em todas as páginas internas
├── src/tests/
│   ├── auth.test.ts           # testes unitários de auth.ts
│   └── login.spec.ts          # testes Playwright do fluxo de login
└── public/
    └── styles/
        └── global.css         # estilos reutilizados na tela de login
```
