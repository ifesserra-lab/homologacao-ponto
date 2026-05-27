# Guia do Usuário — Espelhos de Ponto

## O que é

Aplicativo desktop para consultar e monitorar os espelhos de ponto dos servidores do IFES extraídos diretamente do SIGRH. Os dados ficam armazenados localmente; não é necessária conexão com a internet para visualizar registros já extraídos.

---

## Instalação

### Pré-requisitos

| Requisito | Versão mínima | Onde instalar |
|-----------|--------------|---------------|
| Node.js | 18+ | https://nodejs.org |
| Rust + Cargo | 1.77+ | https://rustup.rs |
| npm | 9+ | incluso com Node.js |

### Passos

```bash
# Clone o repositório
git clone <url-do-repositorio>
cd homologacao_ponto/desktop

# Instale as dependências JavaScript
npm install

# Instale as dependências do crawler
cd src-crawler
npm install
cd ..
```

### Configuração inicial

Crie o arquivo `desktop/.env` (copie de `desktop/.env.example`):

```env
# Caminho absoluto para os dados — ajuste conforme seu sistema
VITE_DATA_DIR=/Users/seu-usuario/homologacao_ponto/data/runs/servidores

# Credenciais SIGRH (usadas pelo crawler para extração)
SIGRH_USERNAME=seu.login.sigrh
SIGRH_PASSWORD=sua.senha.sigrh

# Login do aplicativo (hashes SHA-256)
VITE_USER_HASH=
VITE_PASSWORD_HASH=
```

> **Dica:** `VITE_USER_HASH` e `VITE_PASSWORD_HASH` são os hashes SHA-256 do usuário e senha que você deseja usar para entrar no aplicativo. Podem ser gerados em qualquer ferramenta online de SHA-256.

---

## Iniciando o aplicativo

### Modo desenvolvimento

```bash
cd desktop
npm run tauri dev
```

A janela abre em alguns segundos. Alterações no código Vue recarregam automaticamente.

### Build para distribuição

```bash
cd desktop
npm run tauri build
```

O instalador é gerado em `desktop/src-tauri/target/release/bundle/`.

---

## Navegação

O aplicativo possui cinco abas na barra superior:

| Aba | Descrição |
|-----|-----------|
| **Servidores** | Lista todos os servidores cadastrados com resumo de ocorrências |
| **Indicadores** | Dashboard com métricas globais e detalhadas por servidor |
| **Crawler** | Executa a extração de dados do SIGRH |
| **↻** | Botão para recarregar os dados do disco sem rodar o crawler |
| **⚙** | Configurações (credenciais e lista de servidores) |

---

## Tela Servidores

Lista todos os servidores com:
- Nome e SIAPE
- Último período extraído
- Badge com contagem de ocorrências relevantes

Clique em um servidor para ver o detalhamento completo.

---

## Tela Detalhe do Servidor

Exibe duas abas:

### Aba Série Histórica

Tabela com todos os meses extraídos. Colunas:
- **Período** — mês/ano
- **Dias úteis** — dias trabalhados esperados
- **Faltas** — ausências não justificadas
- **Atrasos** — registros com entrada após horário
- **Saídas antecipadas**
- **Saldo** — saldo acumulado de horas extras/faltas
- **Ocorrências** — contagem total de ocorrências no mês

Clique em qualquer linha para ver o detalhe dia a dia daquele mês.

### Aba Indicadores

Métricas calculadas para o servidor:
- Total de faltas, atrasos, saídas antecipadas no período
- Saldo acumulado de horas extras
- Distribuição de ocorrências por categoria

---

## Tela Detalhe do Mês

Tabela dia a dia com:
- **Data** — dia da semana + data
- **Entrada / Saída** — horários registrados
- **Saldo do dia** — diferença em relação à jornada
- **Ocorrências** — registros de afastamento, licença, etc.

---

## Tela Indicadores

Dashboard com duas abas:

### Global

Visão geral de todos os servidores:
- Contagem total de ocorrências por categoria
- Comparativo entre servidores

### Detalhado

Filtro por servidor e período. Gráficos e tabelas com evolução mensal de cada indicador.

---

## Usando o Crawler

O crawler acessa o SIGRH usando as credenciais do `.env`, navega até a página de espelhos de ponto e extrai os dados de cada servidor × período definido em `servidores.yaml`.

### Passo a passo

1. Verifique que `SIGRH_USERNAME` e `SIGRH_PASSWORD` estão preenchidos em `.env` (ou via Configurações)
2. Clique na aba **Crawler**
3. Clique em **Executar Crawler**
4. Acompanhe o progresso na barra e no log em tempo real
5. Ao concluir, todas as telas são atualizadas automaticamente com os novos dados

### O que o crawler faz

Para cada servidor listado em `servidores.yaml` e para cada ano configurado (ex.: 2025, 2026), o crawler:
1. Navega para o formulário de espelho de ponto no SIGRH
2. Preenche o nome e o período
3. Seleciona o servidor no autocomplete
4. Extrai o HTML da página
5. Salva em `data/runs/servidores/<slug>/espelho-<mês>-<ano>.json`

### Progresso

A barra de progresso mostra `concluídos / total`. O total é `nº de servidores × nº de meses`. Para 5 servidores × 24 meses (2 anos) = 120 extrações.

### Erros comuns

| Erro | Causa provável | Solução |
|------|---------------|---------|
| `SIGRH_USERNAME e SIGRH_PASSWORD são obrigatórios` | `.env` não configurado | Preencher credenciais em Configurações ou no `.env` |
| `Credenciais inválidas` | Login ou senha errados no SIGRH | Verificar credenciais no SIGRH manualmente |
| `Servidor não encontrado nos resultados` | Nome no `servidores.yaml` diferente do SIGRH | Corrigir nome para exatamente como aparece no SIGRH (maiúsculas) |
| `CAPTCHA ou bloqueio anti-automação detectado` | SIGRH bloqueou o acesso | Aguardar alguns minutos e tentar novamente |
| `Sessão expirada` | Timeout do SIGRH | O crawler tentará reconectar na próxima execução |

---

## Configurações

A aba ⚙ permite editar dois arquivos sem sair do aplicativo:

### Credenciais (`.env`)

Campos editáveis:
- `SIGRH_USERNAME` e `SIGRH_PASSWORD` — credenciais para o crawler
- `VITE_DATA_DIR` — caminho para os dados (raramente precisa mudar)
- `VITE_USER_HASH` / `VITE_PASSWORD_HASH` — hash SHA-256 do login do aplicativo

Clique **Salvar** após editar. As credenciais do crawler entram em vigor na próxima execução. As do app (hashes) entram em vigor no próximo login.

### Servidores (`servidores.yaml`)

Exemplo:
```yaml
anos:
  - 2025
  - 2026
servidores:
  - nome: CELIO PROLICIANO MAIOLI
    siape: '1534589'
  - nome: NOVO SERVIDOR AQUI
    siape: '9999999'
```

- `anos` — lista de anos a extrair. Adicione um novo ano para incluir nos próximos crawls.
- `servidores` — lista de servidores. `nome` deve ser exatamente como aparece no SIGRH (letras maiúsculas, sem abreviações).

Clique **Salvar**. Alterações entram em vigor na próxima execução do crawler.

---

## Adicionando um Novo Servidor

1. Vá em **⚙ Configurações**
2. Edite `servidores.yaml` e adicione a entrada com `nome` e `siape`
3. Salve
4. Vá em **Crawler** e execute — os espelhos do novo servidor serão extraídos

---

## Atualizando os Dados Manualmente

Clique no botão **↻** na barra de navegação a qualquer momento para recarregar os dados do disco sem executar o crawler. Útil quando os arquivos JSON foram atualizados externamente (ex.: via `git pull`).

---

## Tema Claro / Escuro

Clique no ícone de lua/sol no canto superior direito para alternar entre tema claro e escuro. A preferência é salva automaticamente.

---

## Estrutura dos Dados

Os espelhos ficam em `data/runs/servidores/`:

```
data/runs/servidores/
├── celio-proliciano-maioli/
│   ├── espelho-janeiro-2025.json
│   ├── espelho-fevereiro-2025.json
│   └── ...
├── gustavo-maia-de-almeida/
│   └── ...
└── ...
```

Cada arquivo JSON contém os dados de um mês de um servidor. O nome da pasta é gerado automaticamente a partir do nome do servidor (minúsculas, acentos removidos, espaços → hífens).

---

## Perguntas Frequentes

**O crawler precisa de internet?**
Sim — ele acessa o SIGRH online para extrair os dados. Mas a visualização dos dados já extraídos funciona offline.

**Preciso rodar o crawler todo dia?**
Não. Os dados ficam salvos. Execute quando quiser atualizar os registros de um período recente.

**O SIGRH mudou o layout e o crawler parou de funcionar.**
Abra uma issue no repositório com o erro do log. A automação usa seletores CSS/texto e pode precisar de ajuste quando o SIGRH é atualizado.

**Posso rodar para anos anteriores?**
Sim. Adicione o ano em `servidores.yaml → anos` e execute o crawler. O SIGRH mantém histórico de períodos passados.

**Os dados ficam seguros?**
Os dados ficam apenas no seu computador, em arquivos JSON locais. Nenhum dado é enviado a servidores externos. As credenciais do SIGRH ficam no arquivo `.env` local.
