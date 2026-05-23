# Especificação: Aplicativo de Crawler com Login SIGRH

**Nome curto**: login-sigrh-crawler

## Visão geral

Criar um aplicativo que permita autenticar-se no portal SIGRH (https://sigrh.ifes.edu.br/sigrh/login.jsf) e, após login bem-sucedido, navegar e coletar informações autorizadas pelo usuário. O foco é fornecer um mecanismo seguro de login automático e um crawler minimal que executa ações autorizadas pelo usuário dentro da sessão autenticada.

## Clarifications

### Session 2026-05-20

- Q: Que páginas/entidades o usuário deseja coletar após login? → A: Apenas apontamentos/registros de ponto do usuário autenticado.
- Q: Onde o resultado do crawl deve ficar depois de extraído? → A: Salvar resultados em arquivo JSON local por execução.
- Q: O que fazer se o SIGRH exigir CAPTCHA, MFA ou bloquear automação? → A: Abortar a execução e informar que a proteção impede automação.
- Q: Quais campos mínimos cada registro de ponto coletado deve conter? → A: Data, horários de entrada/saída, URL origem e data/hora da coleta.
- Q: Como o crawler deve evitar tráfego agressivo contra o SIGRH? → A: Usar intervalo mínimo de 2s entre navegações/ações Playwright e limite de 20 páginas por execução.
- Q: Como reconciliar o intervalo mínimo de 2s e limite de 20 páginas com a meta temporal? → A: Alterar critério de sucesso para execução completa em até 60 segundos.
- Q: O que fazer quando nenhum apontamento de ponto for encontrado? → A: Gerar JSON normalmente com `record_count: 0` e mensagem “nenhum registro encontrado”.
- Q: O que fazer se o arquivo JSON local não puder ser escrito? → A: Encerrar com erro claro e não considerar a execução bem-sucedida.
- Q: Qual terminologia usar para sessão e acessos no plano com Playwright? → A: Usar `BrowserSession` e “navegações/ações Playwright” na spec.
- Q: O que fazer se a `BrowserSession` expirar durante o crawl? → A: Encerrar, salvar JSON parcial com status `partial` e mensagem de sessão expirada.
- Q: Como nomear o arquivo JSON de saída e que identificador do usuário incluir? → A: Salvar em `--output-dir` usando `crawl-result-{run_id}.json`; incluir apenas `username_ref` igual ao nome de usuário informado, sem senha, cookies ou outros identificadores.
- Q: O que fazer com HTML de apontamento inesperado ou malformado? → A: Ignorar registros individuais que não tenham campos mínimos, registrar aviso local sem HTML bruto e continuar; se nenhuma linha válida restar, gerar o resultado vazio definido.
- Q: O que fazer se houver mais páginas de ponto além do limite de 20 páginas? → A: Parar antes da página 21, salvar JSON parcial com status `partial`, preservar registros coletados e informar que o limite de páginas foi atingido.
- Q: O que fazer se o navegador Playwright não estiver instalado ou não iniciar? → A: Encerrar com erro claro de configuração e orientar a instalação dos navegadores antes de qualquer login.
- Q: O modo com navegador visível faz parte do fluxo normal? → A: Não; `--headed` é apenas opção de depuração local, e o padrão deve ser execução sem janela visível.

## Atores

- **Usuário autenticado**: pessoa com credenciais válidas do IFES que autoriza o crawler a acessar seu conteúdo.
- **Sistema SIGRH**: serviço terceiro que exige autenticação via página `login.jsf`.

## Ações principais

- Autenticar usuário usando credenciais fornecidas.
- Manter `BrowserSession` autenticada e navegar por páginas internas.
- Extrair apenas apontamentos/registros de ponto do usuário autenticado.

## Dados envolvidos

- Credenciais do usuário (nome de usuário, senha) — sensíveis.
- Páginas e dados HTML retornados pelo SIGRH relacionados a apontamentos/registros de ponto.

## Restrições e considerações

- O usuário é responsável por possuir autorização para acessar os dados do SIGRH com as credenciais usadas.
- O aplicativo NÃO deve tentar contornar medidas de segurança (CAPTCHAs, MFA) nem violar termos de uso do SIGRH.
- Se o SIGRH exigir CAPTCHA, MFA ou outra proteção anti-automação, o aplicativo deve abortar a execução e informar que a proteção impede automação.
- Armazenamento de credenciais deve ser seguro e opcional — por padrão, não persistir sem consentimento explícito.

## Cenários de usuário & Testes

### Cenário 1 — Login básico

- Dado que o usuário fornece credenciais válidas
- Quando o aplicativo submete o formulário de login em `login.jsf`
- Então o usuário vê a tela inicial autenticada do SIGRH e o crawler marca o estado como `autenticado`.

Teste (TDD): escrever teste que mocka a resposta HTTP do servidor retornando página pós-login e valida mudança de estado.

### Cenário 2 — Falha de autenticação

- Dado que o usuário fornece credenciais inválidas
- Quando o aplicativo submete o formulário de login
- Então o sistema retorna erro de autenticação e não inicia o crawler.

Teste (TDD): simular resposta de erro e validar mensagem de erro tratada.

### Cenário 3 — Crawl após login

- Dado que a `BrowserSession` está autenticada
- Quando o usuário solicita a coleta de apontamentos/registros de ponto
- Então o crawler visita as URLs autorizadas e salva os dados extraídos em um arquivo JSON local da execução.

Teste (TDD): mockar páginas internas e validar que o crawler segue links permitidos e extrai campos esperados.

## Requisitos funcionais (testáveis)

1. O sistema deve permitir que o usuário inicie login fornecendo credenciais via arquivo `.env` (variáveis `SIGRH_USERNAME` e `SIGRH_PASSWORD`). Se o arquivo `.env` não estiver presente, o sistema deve solicitar as credenciais de forma interativa no início da execução.
   - Aceitação: teste que define as variáveis de ambiente simuladas e valida transição para estado autenticado; teste adicional que fornece credenciais via prompt interativo quando `.env` ausente.

2. O sistema deve detectar sucesso ou falha de login com mensagens claras.
   - Aceitação: teste que valida mensagens de sucesso/erro conforme resposta mockada.

3. O sistema deve manter uma `BrowserSession` autenticada para navegações/ações Playwright subsequentes durante a execução do crawler.
   - Aceitação: teste que verifica preservação de sessão autenticada no contexto de navegador usado pelas navegações/ações Playwright subsequentes mockadas.

4. O sistema deve limitar a coleta pós-login aos apontamentos/registros de ponto do usuário autenticado.
   - Aceitação: teste que valida que o crawler visita apenas URLs relacionadas a apontamentos/registros de ponto e rejeita URLs fora desse escopo.

5. O sistema deve salvar os apontamentos/registros de ponto coletados em um arquivo JSON local por execução.
   - Aceitação: teste que valida criação de um arquivo JSON local contendo os registros extraídos e metadados da execução.
   - Cada registro deve conter, no mínimo, data do ponto, horários de entrada/saída disponíveis, URL de origem e data/hora da coleta.
   - O arquivo deve ser criado no diretório de saída configurado e usar o padrão `crawl-result-{run_id}.json`.
   - O metadado `username_ref` deve conter apenas o nome de usuário fornecido, sem senha, cookies, matrícula adicional inferida ou outros identificadores sensíveis.
   - Se nenhum apontamento for encontrado, o sistema deve gerar JSON válido com `record_count: 0`, lista de registros vazia e mensagem “nenhum registro encontrado”.
   - Se o arquivo JSON local não puder ser escrito, o sistema deve encerrar com erro claro e não considerar a execução bem-sucedida.
   - Se a `BrowserSession` expirar durante o crawl, o sistema deve encerrar a coleta, salvar JSON parcial com status `partial`, preservar registros já coletados e incluir mensagem de sessão expirada.
   - Se o limite de 20 páginas for atingido antes do fim da paginação de apontamentos, o sistema deve parar antes de visitar a página 21, salvar JSON parcial com status `partial`, preservar registros já coletados e incluir mensagem de limite atingido.
   - Se uma página ou linha de apontamento tiver HTML inesperado ou malformado, o sistema deve ignorar apenas o registro sem campos mínimos, registrar aviso local sem HTML bruto e continuar com os demais registros válidos.

6. O sistema NÃO deve armazenar credenciais por padrão; armazenamento só com consentimento explícito do usuário.
   - Aceitação: teste que verifica ausência de arquivo de credenciais quando consentimento não dado.

7. O sistema deve registrar eventos de sucesso/falha e erros em log acessível localmente para diagnóstico.
   - Aceitação: teste que valida entradas de log para eventos simulados.

8. O sistema deve abortar a execução quando detectar CAPTCHA, MFA ou bloqueio anti-automação do SIGRH.
   - Aceitação: teste que simula resposta com proteção anti-automação e valida que o crawler não tenta contornar a proteção, não coleta dados e informa o motivo ao usuário.

9. O sistema deve respeitar intervalo mínimo de 2 segundos entre navegações/ações Playwright que acessem o SIGRH e limitar cada execução a no máximo 20 páginas visitadas.
   - Aceitação: teste que simula múltiplas páginas e valida espaçamento mínimo entre navegações/ações Playwright e interrupção ao atingir o limite de 20 páginas.

10. O sistema deve encerrar com erro claro de configuração quando o navegador necessário para automação não estiver instalado ou não puder iniciar.
   - Aceitação: teste que simula falha de inicialização do navegador e valida mensagem orientando instalar os navegadores antes de qualquer tentativa de login.

## Critérios de sucesso

- 95% dos logins com credenciais válidas resultam em sessão autenticada em ambiente de teste controlado.
- O crawler executa o escopo definido sem acessar URLs fora do escopo em 100% dos testes automatizados.
- Usuário pode iniciar uma execução completa (login + crawl) em até 60 segundos em conexões normais, considerando o intervalo mínimo de 2 segundos entre navegações/ações Playwright e o limite de 20 páginas.

## Entidades-chave

- `Credential` — armazenar nome de usuário e senha em memória ou armazenamento seguro (opcional).
- `BrowserSession` — contexto de navegador autenticado mantido durante a execução.
- `CrawlScope` — regras/URLs permitidas para apontamentos/registros de ponto.
- `CrawlResult` — estrutura contendo apontamentos/registros de ponto extraídos, metadados da execução e caminho do arquivo JSON local gerado.
- `AttendanceRecord` — registro de ponto contendo data do ponto, horários de entrada/saída disponíveis, URL de origem e data/hora da coleta.

## Saída dos resultados

Cada execução do crawler deve gerar um arquivo JSON local com os apontamentos/registros de ponto coletados. O arquivo deve conter os registros extraídos e metadados mínimos da execução, como data/hora da coleta, usuário de referência sem senha e quantidade de registros.

O arquivo deve ser salvo no diretório de saída configurado, por padrão `./data/runs`, com nome `crawl-result-{run_id}.json`. O `run_id` deve ser único por execução. O campo `username_ref` deve conter apenas o nome de usuário usado para login, sem senha, cookies, matrícula adicional inferida, HTML bruto ou tokens de sessão.

Quando nenhum apontamento de ponto for encontrado, o arquivo JSON ainda deve ser gerado com `record_count: 0`, lista de registros vazia e mensagem “nenhum registro encontrado”.

Se o arquivo JSON local não puder ser escrito, a execução deve terminar como falha com mensagem clara ao usuário. O sistema não deve tratar a coleta como bem-sucedida sem persistir o arquivo de saída.

Se a `BrowserSession` expirar durante o crawl, a execução deve encerrar sem tentar reautenticação automática. O arquivo JSON deve ser salvo com status `partial`, registros já coletados e mensagem de sessão expirada.

Se a paginação de apontamentos ainda tiver páginas disponíveis ao atingir 20 páginas visitadas, a execução deve parar antes da página 21 e salvar JSON com status `partial`, registros já coletados e mensagem de limite de páginas atingido.

Se a estrutura HTML de uma página de apontamentos estiver inesperada ou malformada, o sistema deve ignorar registros individuais que não tenham os campos mínimos obrigatórios, registrar aviso local sem persistir HTML bruto e continuar extraindo registros válidos. Se nenhum registro válido for extraído, aplica-se o comportamento de resultado vazio.

Cada registro de ponto no JSON deve conter, no mínimo:

- Data do ponto.
- Horários de entrada/saída disponíveis.
- URL de origem no SIGRH.
- Data/hora da coleta.

## Assunções

- O usuário tem conta válida no SIGRH e autorização para usar suas credenciais.
- O SIGRH usa autenticação baseada em formulário HTML acessível via `login.jsf` sem MFA obrigatória para o usuário alvo.
- O projeto seguirá TDD: testes escritos antes da implementação (unit + integração com mocks).

## Credenciais e `.env` (resolvido)

As credenciais serão fornecidas via arquivo `.env` usando as variáveis `SIGRH_USERNAME` e `SIGRH_PASSWORD`. Comportamento esperado:

- Se `.env` existir e contiver as variáveis, o aplicativo deve carregar as credenciais da variável de ambiente no início da execução.
- Se `.env` não existir ou as variáveis não estiverem definidas, o aplicativo deve solicitar credenciais de forma interativa.
- Por padrão, o aplicativo NÃO deve persistir credenciais em outros arquivos locais sem consentimento explícito do usuário.
- O projeto deve documentar claramente que arquivos `.env` contendo credenciais NÃO devem ser commitados ao controle de versão e devem ser protegidos pelo usuário.

Aceitação: teste que define variáveis de ambiente simuladas e valida login; teste que verifica que nenhum arquivo adicional de credenciais é criado sem consentimento.

## Escopo do crawling

O crawler deve coletar apenas apontamentos/registros de ponto do usuário autenticado. Horários, escalas, relatórios acadêmicos, relatórios administrativos e outras páginas internas ficam fora do escopo inicial, salvo se uma especificação futura ampliar o escopo.

## Observações de segurança e conformidade

- Implementar proteção contra vazamento de credenciais (não logar senhas, usar armazenamento seguro se habilitado).
- Evitar técnicas que driblem CAPTCHAs ou proteções anti-bot; se encontradas, reportar ao usuário e abortar.
- CAPTCHA, MFA ou bloqueio anti-automação devem encerrar a execução sem novas tentativas automáticas.
- O crawler deve usar intervalo mínimo de 2 segundos entre navegações/ações Playwright que acessem o SIGRH e visitar no máximo 20 páginas por execução.
- Traces, screenshots, HTML bruto, cookies e artefatos de navegador não devem ser persistidos por padrão porque podem conter dados sensíveis.
- A opção de navegador visível é apenas para depuração local; a execução normal deve usar navegador sem janela visível.

---

Especificação gerada automaticamente.
