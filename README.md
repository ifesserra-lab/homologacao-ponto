# Homologacao Ponto

Ferramenta para exportar o Espelho de Ponto do SIGRH para JSON e visualizá-lo
em um dashboard estático. Usa Playwright para navegar o SIGRH de forma headless,
extrai os dados visíveis e os persiste em `data/runs/servidores/`.

## Setup

```bash
python3.12 -m venv .venv
. .venv/bin/activate
pip install -e ".[dev]"
playwright install chromium
```

Copie `.env.example` para `.env` e preencha:

```bash
cp .env.example .env
```

```text
# Credenciais SIGRH (para o scraper)
SIGRH_USERNAME=<matricula>
SIGRH_PASSWORD=<senha>

# Credenciais do dashboard (para a tela de login)
DASHBOARD_USER=<usuario>
DASHBOARD_PASSWORD=<senha>
```

Para o dashboard, calcule os hashes SHA-256 e adicione ao `.env`:

```bash
export DASHBOARD_USER=<usuario>
export DASHBOARD_PASSWORD=<senha>
export PUBLIC_DASHBOARD_USER_HASH=$(python3 -c "import hashlib,os; print(hashlib.sha256(os.environ['DASHBOARD_USER'].encode()).hexdigest())")
export PUBLIC_DASHBOARD_PASSWORD_HASH=$(python3 -c "import hashlib,os; print(hashlib.sha256(os.environ['DASHBOARD_PASSWORD'].encode()).hexdigest())")
```

## Uso rápido (Makefile)

```bash
make export      # exporta espelho de todos os servidores em servidores.yaml
make dashboard   # sobe o dashboard local em http://localhost:4321
make test        # roda a suite de testes Python
```

## Exportar espelho

### Batch (recomendado)

Edite `servidores.yaml` com a lista de servidores e o período:

```yaml
anos: [2026]
servidores:
  - nome: "NOME COMPLETO EM MAIÚSCULAS"
    siape: "1234567"
```

Execute:

```bash
homologacao-ponto batch --file servidores.yaml --output-dir data/runs
```

Os JSONs são salvos em `data/runs/servidores/<slug-nome>/espelho-<periodo>.json`.

### Servidor único

```bash
homologacao-ponto espelho-ponto --servidor "NOME DO SERVIDOR" --output-dir data/runs
```

## Dashboard

```bash
# Instalar dependências (primeira vez)
cd dashboard && npm install

# Subir em desenvolvimento
make dashboard   # ou: cd dashboard && npm run dev
```

Acesse `http://localhost:4321`. Login com as credenciais definidas em `DASHBOARD_USER` / `DASHBOARD_PASSWORD`.

### Build para produção

```bash
cd dashboard && npm run build
```

## GitHub Actions

Dois workflows automáticos:

| Workflow | Gatilho | O que faz |
|---------|---------|-----------|
| `export.yml` | Toda segunda-feira 08h UTC + `workflow_dispatch` | Roda `homologacao-ponto batch`, comita JSONs atualizados em `data/runs/servidores/` |
| `deploy.yml` | Push em `main` (data ou dashboard alterados) + `workflow_dispatch` | Build Astro + deploy no GitHub Pages |

### Configuração do repositório (uma vez)

1. **Tornar público**: Settings → Danger Zone → Change visibility → Public
2. **GitHub Pages**: Settings → Pages → Source → GitHub Actions
3. **Secrets** (Settings → Secrets and variables → Actions):

| Secret | Descrição |
|--------|-----------|
| `SIGRH_USERNAME` | Matrícula SIGRH para o scraper |
| `SIGRH_PASSWORD` | Senha SIGRH para o scraper |
| `DASHBOARD_USER` | Usuário para login no dashboard |
| `DASHBOARD_PASSWORD` | Senha para login no dashboard |

O workflow de deploy calcula os hashes automaticamente a partir de `DASHBOARD_USER` e `DASHBOARD_PASSWORD`.

## Estrutura de dados

```text
data/runs/servidores/
└── <slug-nome>/
    ├── espelho-janeiro-2026.json
    ├── espelho-fevereiro-2026.json
    └── ...
```

Schema completo em [`docs/espelho-ponto-schema.yaml`](docs/espelho-ponto-schema.yaml) (schema v2 com campo `resumo`).

## Testes

```bash
make test                    # suite Python completa
cd dashboard && npm test     # testes TypeScript (vitest)
```

## Códigos de saída do CLI

| Código | Significado |
|--------|------------|
| `0` | Sucesso |
| `2` | Falha de autenticação |
| `3` | CAPTCHA/MFA, navegação inválida ou erro inesperado |
| `4` | Falha de escopo, seleção ou divergência de servidor |
| `5` | Falha de escrita JSON ou CAPTCHA durante exportação |
| `6` | JSON parcial ou sessão expirada |
| `7` | Playwright/Chromium ausente |

O crawler não contorna CAPTCHA, MFA nem bloqueios anti-automação.
