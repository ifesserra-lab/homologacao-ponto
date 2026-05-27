# Espelhos de Ponto — IFES

Aplicativo desktop para extrair e visualizar os espelhos de ponto dos servidores diretamente do [SIGRH do IFES](https://sigrh.ifes.edu.br). Os dados ficam armazenados localmente em JSON; não é necessária conexão para consultar registros já extraídos.

## Stack

| Camada | Tecnologia |
|--------|-----------|
| Shell desktop | [Tauri 2](https://tauri.app) (Rust) |
| Frontend | Vue 3 + Vite + TypeScript |
| Estado | Pinia |
| Crawler | Node.js + [Playwright](https://playwright.dev) |
| Dados | JSON em disco |

## Pré-requisitos

- [Node.js](https://nodejs.org) ≥ 18
- [Rust + Cargo](https://rustup.rs) ≥ 1.77

## Instalação

```bash
git clone https://github.com/ifesserra-lab/homologacao-ponto.git
cd homologacao-ponto/desktop

# Dependências do frontend e do crawler
npm install
cd src-crawler && npm install && cd ..
```

## Configuração

Copie o arquivo de exemplo e preencha:

```bash
cp .env.example .env
```

```env
# Caminho absoluto para os dados (ajuste ao seu sistema)
VITE_DATA_DIR=/Users/seu-usuario/homologacao-ponto/data/runs/servidores

# Credenciais SIGRH usadas pelo crawler
SIGRH_USERNAME=seu.login
SIGRH_PASSWORD=sua.senha

# Login do aplicativo — hashes SHA-256 do usuário e senha desejados
VITE_USER_HASH=<sha256 do usuario>
VITE_PASSWORD_HASH=<sha256 da senha>
```

Para gerar os hashes:

```bash
echo -n "meu-usuario" | shasum -a 256
echo -n "minha-senha"  | shasum -a 256
```

## Executando em desenvolvimento

```bash
cd desktop
npm run tauri dev
```

## Servidores monitorados

Edite `servidores.yaml` na raiz do repositório para definir quais servidores e anos extrair:

```yaml
anos:
  - 2025
  - 2026
servidores:
  - nome: CELIO PROLICIANO MAIOLI
    siape: '1534589'
  - nome: GUSTAVO MAIA DE ALMEIDA
    siape: '2701647'
```

O campo `nome` deve ser exatamente como aparece no SIGRH (maiúsculas).

## Usando o Crawler

1. Certifique-se que `SIGRH_USERNAME` e `SIGRH_PASSWORD` estão preenchidos
2. No app, clique na aba **Crawler**
3. Clique em **Executar Crawler**
4. Acompanhe o progresso — ao concluir, todas as telas são atualizadas automaticamente

O crawler extrai todos os espelhos de `servidores × anos × 12 meses` e salva em:

```
data/runs/servidores/
└── celio-proliciano-maioli/
│   ├── espelho-janeiro-2025.json
│   ├── espelho-fevereiro-2025.json
│   └── ...
└── gustavo-maia-de-almeida/
    └── ...
```

### Execução via linha de comando (sem o app)

```bash
# Batch completo (usa servidores.yaml)
node desktop/src-crawler/cli.js batch \
  --file servidores.yaml \
  --output-dir data/runs \
  --env-file desktop/.env

# Servidor e mês específicos
node desktop/src-crawler/cli.js espelho \
  --servidor "NOME DO SERVIDOR" \
  --siape 1234567 \
  --mes 5 \
  --ano 2025 \
  --output-dir data/runs \
  --env-file desktop/.env

# Modo headed (exibe o browser — útil para depurar)
node desktop/src-crawler/cli.js batch --file servidores.yaml --headed
```

## Build para distribuição

```bash
cd desktop
npm run tauri build
```

O instalador é gerado em `desktop/src-tauri/target/release/bundle/`.

> **Nota:** o binário empacotado do crawler (`src-tauri/binaries/crawler-*`) precisa ser gerado separadamente com `node scripts/bundle-crawler.mjs` antes do build de release. Veja [docs/TECHNICAL.md](docs/TECHNICAL.md) para detalhes.

## Documentação

| Documento | Conteúdo |
|-----------|---------|
| [docs/TECHNICAL.md](docs/TECHNICAL.md) | Arquitetura, fluxo de dados, comandos Tauri, decisões de design |
| [docs/USUARIO.md](docs/USUARIO.md) | Guia completo de uso do aplicativo |
| [docs/espelho-ponto-schema.yaml](docs/espelho-ponto-schema.yaml) | Schema dos arquivos JSON de espelho |

## Estrutura do repositório

```
homologacao-ponto/
├── desktop/              # App Tauri (Vue 3 + Rust + Node.js crawler)
│   ├── src/              # Frontend Vue 3
│   ├── src-tauri/        # Backend Rust (comandos, eventos)
│   └── src-crawler/      # Crawler Node.js + Playwright
├── data/runs/servidores/ # Espelhos extraídos (JSON por servidor/mês)
├── docs/                 # Documentação técnica e de usuário
├── specs/                # Especificações de features
└── servidores.yaml       # Lista de servidores e anos a extrair
```
