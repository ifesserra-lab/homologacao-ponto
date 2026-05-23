# Homologacao Ponto

CLI Python para autenticar no SIGRH com Playwright e coletar apenas registros
de ponto do usuário autenticado em um JSON local por execução. Também inclui um
fluxo para navegar até a tela "Espelho do Ponto" após login. Quando informado
um servidor, o fluxo busca e seleciona o resultado único, abre o espelho diário
individual e exporta os dados visíveis para JSON.

## Setup

```bash
python3.12 -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
python -m playwright install chromium
```

Crie um `.env` local a partir de `.env.example` e preencha:

```text
SIGRH_USERNAME=<usuario>
SIGRH_PASSWORD=<senha>
```

Credenciais, `.env`, cookies, traces, screenshots e HTML bruto não devem ser
commitados ou persistidos por padrão.

## Uso

```bash
homologacao-ponto crawl --output-dir ./data/runs
```

Para navegar até a tela "Espelho do Ponto":

```bash
homologacao-ponto espelho-ponto --output-dir ./data/runs
```

Para buscar e selecionar um servidor na tela "Espelho do Ponto" e exportar o
espelho diário visível em JSON:

```bash
homologacao-ponto espelho-ponto --servidor "Celio Proliciano Maioli" --output-dir ./data/runs
```

Esse comando gera, quando a seleção e exportação terminam com sucesso:

```text
data/runs/selection-result-{run_id}.json
data/runs/espelho-ponto-{run_id}.json
data/runs/export-result-{run_id}.json
```

O arquivo `espelho-ponto-{run_id}.json` contém servidor, período visível,
data/hora de captura, mensagens da página e registros por dia com `data`,
`marcacoes`, `ocorrencias`, `observacoes` e `textos_visiveis` quando esses
campos estiverem visíveis. HTML bruto, screenshots, cookies, senhas, tokens e
traces não são persistidos por padrão.

Para depuração local com navegador visível:

```bash
homologacao-ponto crawl --headed --output-dir ./data/runs
homologacao-ponto espelho-ponto --headed --output-dir ./data/runs
homologacao-ponto espelho-ponto --servidor "Celio Proliciano Maioli" --headed --output-dir ./data/runs
```

`--headed` é apenas debug; o padrão é headless.

## Códigos De Saída

- `0`: sucesso ou resultado vazio persistido.
- `2`: falha de autenticação.
- `3`: CAPTCHA/MFA no login, falha de navegação, página inválida ou erro
  inesperado de exportação.
- `4`: falha de escopo, limite operacional, parcial por limite de páginas ou
  falha de navegação até "Espelho do Ponto", falha de seleção de servidor ou
  divergência entre servidor solicitado e página do espelho.
- `5`: falha ao escrever JSON local em fluxos existentes ou CAPTCHA/MFA durante
  exportação.
- `6`: falha ao escrever JSON local ou `BrowserSession` expirada durante crawl,
  navegação ou seleção com JSON parcial.
- `7`: navegador Playwright ausente ou não inicializado.

O crawler não tenta contornar CAPTCHA, MFA ou bloqueios anti-automação.

## Testes

```bash
pytest
```

Detalhes do fluxo planejado estão em
`specs/001-login-sigrh/quickstart.md` e
`specs/002-navegar-espelho-ponto/quickstart.md` e
`specs/003-selecionar-servidor/quickstart.md` e
`specs/004-baixar-espelho-json/quickstart.md`.
