# Backlog de Features — homologacao-ponto

> Atualizado automaticamente pelo skill `speckit-specify` a cada nova feature.
> Fonte: diretórios em `specs/`.

---

## Resumo

| EPIC | Features | User Stories | Implemented | In Progress | Draft |
|------|----------|-------------|-------------|-------------|-------|
| EPIC-1 · Acesso ao SIGRH | 1 | 3 | 1 | 0 | 0 |
| EPIC-2 · Navegação e Seleção | 2 | 6 | 2 | 0 | 0 |
| EPIC-3 · Exportação do Espelho | 3 | 9 | 3 | 0 | 0 |
| EPIC-4 · Batch Avançado | 1 | 3 | 1 | 0 | 0 |
| **Total** | **7** | **21** | **7** | **0** | **0** |

---

## EPIC-1 · Acesso ao SIGRH

Autenticação e login na plataforma SIGRH do IFES.

| # | Spec | Descrição | User Stories | Status |
|---|------|-----------|-------------|--------|
| 001 | [001-login-sigrh](../../specs/001-login-sigrh/) | Login automatizado com credenciais do SIGRH; coleta HTML após autenticação | US1: Login básico · US2: Falha de autenticação · US3: Crawl após login | Implemented |

---

## EPIC-2 · Navegação e Seleção de Servidor

Navegar pelo menu do SIGRH até o Espelho de Ponto e localizar o servidor desejado.

| # | Spec | Descrição | User Stories | Status |
|---|------|-----------|-------------|--------|
| 002 | [002-navegar-espelho-ponto](../../specs/002-navegar-espelho-ponto/) | Navega pelo menu do SIGRH até chegar na tela do Espelho de Ponto | US1 (P1): Acessar espelho após login · US2 (P2): Informar bloqueio ou menu ausente · US3 (P3): Registrar resultado da navegação | Implemented |
| 003 | [003-selecionar-servidor](../../specs/003-selecionar-servidor/) | Busca o servidor pelo nome, seleciona mês/ano e clica em "Selecionar Servidor" | US1 (P1): Abrir espelho do servidor encontrado · US2 (P2): Informar falha de seleção · US3 (P3): Registrar resultado da seleção | Implemented |

---

## EPIC-3 · Exportação do Espelho de Ponto

Capturar os dados visíveis do espelho e salvar em JSON estruturado por servidor.

| # | Spec | Descrição | User Stories | Status |
|---|------|-----------|-------------|--------|
| 004 | [004-baixar-espelho-json](../../specs/004-baixar-espelho-json/) | Captura HTML do espelho após seleção do servidor e exporta campos básicos do dia em JSON | US1 (P1): Gerar JSON do espelho selecionado · US2 (P2): Tratar espelho vazio ou incompleto · US3 (P3): Registrar resultado da exportação | Implemented |
| 005 | [005-exportar-espelho-json](../../specs/005-exportar-espelho-json/) | Captura todos os campos calculados da tabela (HR, HC, HE, HA, HH, Crédito, Débito, Saldo, DNC) e organiza arquivos em pasta por servidor | US1 (P1): Capturar campos calculados da tabela · US2 (P1): Organizar JSON em pasta por servidor · US3 (P2): Preservar compatibilidade com schema anterior | Implemented |
| 006 | [006-batch-yaml-servidores](../../specs/006-batch-yaml-servidores/) | Lê arquivo YAML com lista de servidores e baixa espelho de ponto de cada um em sequência, com relatório consolidado | US1 (P1): Baixar lote via YAML · US2 (P2): Continuar após falha parcial · US3 (P3): Relatório consolidado | Implemented |

---

## EPIC-4 · Batch Avançado

Expansão do batch YAML para suportar períodos históricos por ano ou histórico completo do servidor.

| # | Spec | Descrição | User Stories | Status |
|---|------|-----------|-------------|--------|
| 007 | [007-batch-periodo-anos](../../specs/007-batch-periodo-anos/) | Suporte a campo `anos` no YAML: lista de anos expande para 12 meses cada; `All` baixa histórico completo desde admissão | US1 (P1): Anos específicos · US2 (P2): All (histórico completo) · US3 (P3): Compatibilidade com formato anterior | Implemented |

---

## Legenda

| Campo | Significado |
|-------|------------|
| Spec | Link para o diretório da spec em `specs/` |
| Status | Implemented · In Progress · Draft · Cancelled |
| User Stories | Resumo das USs com prioridade (P1 = crítico, P2 = importante, P3 = desejável) |

## Como atualizar

`speckit-specify` atualiza este arquivo automaticamente ao criar uma nova feature.
Adicione a feature na EPIC correspondente ou crie uma nova EPIC quando o contexto mudar.
