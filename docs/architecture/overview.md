# Visão Geral da Arquitetura — homologacao-ponto

## Propósito

`homologacao-ponto` é uma ferramenta CLI que automatiza a extração do **Espelho de Ponto** do sistema SIGRH (ifes.edu.br), salvando os dados estruturados em JSON para auditoria de frequência de servidores públicos.

## Diagrama de Componentes

```
┌─────────────────────────────────────────────────────────┐
│  CLI (cli.py)                                           │
│  Ponto de entrada; parse de args; imprime resultado     │
└────────────────────┬────────────────────────────────────┘
                     │
┌────────────────────▼────────────────────────────────────┐
│  HomologacaoPontoApp (app.py)                           │
│  Orquestrador: login → navegação → seleção → exportação │
└──┬──────────┬──────────┬──────────┬─────────────────────┘
   │          │          │          │
   ▼          ▼          ▼          ▼
AuthSvc  NavSvc    SelectSvc   EspelhoExportSvc
   │          │          │          │
   └──────────┴──────────┴──────────┘
                     │
          ┌──────────▼──────────┐
          │   SigrhBrowser      │  ← Playwright (infraestrutura)
          │ (sigrh_browser.py)  │
          └──────────┬──────────┘
                     │
          ┌──────────▼──────────┐
          │     SIGRH Web       │  ← sistema externo
          └─────────────────────┘

          ┌──────────────────────┐
          │  EspelhoPontoParser  │  ← HTML → domain objects
          └──────────────────────┘

          ┌──────────────────────┐
          │   ResultWriter       │  ← persiste JSON em disco
          └──────────────────────┘
```

## Principais Módulos

| Módulo | Responsabilidade |
|--------|-----------------|
| `cli.py` | Interface de linha de comando; argumentos; saída para o usuário |
| `app.py` | Orquestração do fluxo completo; composição de serviços |
| `services/authentication_service.py` | Login no SIGRH |
| `services/menu_navigation_service.py` | Navegação via menu até Espelho do Ponto |
| `services/server_selection_service.py` | Busca e seleção do servidor no formulário |
| `services/espelho_export_service.py` | Captura snapshot HTML, parseia, persiste JSON |
| `services/result_writer.py` | Escrita de qualquer resultado; roteia espelhos para `data/servidores/{slug}/` |
| `infrastructure/sigrh_browser.py` | Wrapper Playwright para interações SIGRH |
| `infrastructure/espelho_ponto_parser.py` | Parser HTML → `EspelhoPontoExport` |
| `models/` | Domain objects imutáveis (frozen dataclasses) |

## Tecnologias

| Tecnologia | Uso |
|-----------|-----|
| Python 3.12+ | Linguagem única (runtime, testes, scripts) |
| Playwright | Automação de browser headless/headed |
| pytest | Suite de testes; TDD red/green/refactor |
| html.parser (stdlib) | Parsing de HTML sem dependências externas |
| pathlib (stdlib) | Manipulação de caminhos de arquivo |
| python-dotenv | Leitura de credenciais de `.env` |

## Convenções

- **Domain objects são imutáveis** — `@dataclass(frozen=True)` em todos os modelos
- **Sistemas externos acessados por adapters** — `SigrhBrowser` é substituível por fake em testes
- **Dependências injetadas via construtor** — serviços recebem `browser`, `logger`, `result_writer` externamente
- **Persistência centralizada** — `ResultWriter` é o único gateway de escrita em disco
