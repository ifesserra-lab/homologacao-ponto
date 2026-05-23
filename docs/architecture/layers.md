# Camadas da Arquitetura

## Estrutura de Diretórios

```
src/homologacao_ponto/
├── cli.py                        # Camada de entrada (CLI)
├── app.py                        # Camada de aplicação (orquestrador)
├── models/                       # Camada de domínio
│   ├── espelho_ponto_export.py   #   EspelhoPontoExport, RegistroDiaPonto, ServidorSelecionado
│   ├── espelho_export_result.py  #   ExportacaoEspelhoResult
│   ├── server_selection.py       #   ServidorConsulta, ServidorResultado
│   ├── server_selection_result.py#   SelecaoServidorResult
│   ├── navigation_result.py      #   NavigationResult
│   ├── crawl_result.py           #   CrawlResult
│   ├── browser_session.py        #   BrowserSession
│   └── credential.py             #   Credential
├── services/                     # Camada de serviços de domínio
│   ├── authentication_service.py
│   ├── menu_navigation_service.py
│   ├── server_selection_service.py
│   ├── espelho_export_service.py
│   ├── crawler_service.py
│   └── result_writer.py
└── infrastructure/               # Camada de infraestrutura
    ├── sigrh_browser.py          #   Adapter Playwright
    ├── espelho_ponto_parser.py   #   Parser HTML
    ├── attendance_parser.py      #   SigrhPageSnapshot
    ├── credential_provider.py    #   Leitura de .env
    └── logging.py                #   Configuração de logs
```

## Camada de Domínio (`models/`)

Contém os **objetos de valor** e **entidades** do negócio. Regras:

- Todos são `@dataclass(frozen=True)` — imutáveis por design
- Sem dependências de infra ou serviços externos
- Cada modelo expõe `to_dict()` e `output_filename` quando persistível
- Validação em `__post_init__`: levanta `ValueError` para dados inválidos

Modelos principais:

| Classe | Papel |
|--------|-------|
| `RegistroDiaPonto` | Um dia do espelho; campos de marcações, horas calculadas |
| `EspelhoPontoExport` | Agregado raiz; lista de registros + metadados do servidor |
| `ServidorSelecionado` | Identificação do servidor no espelho |
| `ExportacaoEspelhoResult` | Resultado da operação de exportação |
| `SelecaoServidorResult` | Resultado da operação de seleção de servidor |
| `BrowserSession` | Token de sessão autenticada |

## Camada de Serviços (`services/`)

Implementa os **casos de uso**. Cada serviço:

- Recebe dependências externas no construtor (browser, logger, writer)
- Opera sobre domain objects — não sabe de HTML ou SQL
- Retorna domain objects imutáveis
- É testável com fakes no lugar do browser real

Fluxo de serviços (em ordem de execução):

```
AuthenticationService.login()
    → MenuNavigationService.navigate_to_espelho()
        → ServerSelectionService.select_server()
            → EspelhoExportService.export()
                → ResultWriter.write()
```

## Camada de Infraestrutura (`infrastructure/`)

Adapters para sistemas externos. Regras:

- `SigrhBrowser` encapsula toda interação Playwright — nunca use `page` diretamente fora daqui
- `EspelhoPontoParser` transforma HTML bruto em domain objects — sem efeitos colaterais
- `CredentialProvider` lê `.env` — único ponto de acesso a credenciais

### SigrhBrowser — Contrato Público

| Método | Responsabilidade |
|--------|-----------------|
| `login(credential)` | Autentica e retorna `SigrhLoginResult` |
| `navigate_menu(steps)` | Clica sequência de links de menu |
| `search_server_results(name, ...)` | Preenche formulário de busca, retorna snapshot |
| `capture_espelho_snapshot()` | Captura HTML da página do espelho |
| `goto(url)` | Navegação direta por URL |
| `is_session_expired(html)` | Detecta sessão expirada |
| `is_anti_automation(html)` | Detecta proteção anti-automação |
| `close()` | Fecha browser |

## Camada de Entrada (`cli.py`)

Parse de argumentos com `argparse`. Cria `HomologacaoPontoApp` via `create_app()` e imprime resultado. Responsável por:

- Validação de argumentos de entrada
- Formatação de saída para o usuário
- Mapeamento de `AppResult.exit_code` para código de saída do processo

## Testes

```
tests/
├── contract/    # Contratos CLI e JSON schema — black-box
├── integration/ # Persistência, browser com fakes
└── unit/        # Parser, modelos, lógica de serviço isolada
fixtures/        # HTML estático, snapshots, amostras reutilizáveis
```

**Regra**: sistemas externos (Playwright, .env, disco) são substituídos por fakes em todos os testes automatizados.
