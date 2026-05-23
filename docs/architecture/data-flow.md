# Fluxo de Dados — Extração do Espelho de Ponto

## Fluxo Principal

```
Usuário
  │  homologacao-ponto espelho-ponto --servidor "CELIO ..." --mes 12 --ano 2025 --siape 1534589
  ▼
cli.py → create_app() → HomologacaoPontoApp.run_espelho_ponto()
  │
  ├─ 1. CredentialProvider.load()
  │      Lê SIGRH_USERNAME / SIGRH_PASSWORD de .env
  │      → Credential
  │
  ├─ 2. AuthenticationService.login(credential)
  │      SigrhBrowser.login() via Playwright
  │      → BrowserSession (estado: AUTHENTICATED)
  │
  ├─ 3. MenuNavigationService.navigate_to_espelho(session)
  │      Clica: Módulos → Frequência → Espelho do Ponto
  │      → NavigationResult
  │      (fallback: goto() direto na URL do espelho)
  │
  ├─ 4. ServerSelectionService.select_server(session, request)
  │      a. Digita nome no autocomplete RichFaces
  │      b. Aguarda sugestões → clica no item com SIAPE correto
  │      c. Seleciona mês/ano
  │      d. Clica Buscar
  │      e. Clica "Selecionar Servidor" na listagem
  │      → SelecaoServidorResult
  │
  ├─ 5. EspelhoExportService.export(session, request)
  │      a. SigrhBrowser.capture_espelho_snapshot()
  │         → SigrhPageSnapshot (HTML bruto)
  │      b. EspelhoPontoParser.parse(snapshot)
  │         → EspelhoPontoExport (domain object)
  │      c. ResultWriter.write(export)
  │         → data/servidores/{slug}/espelho-{periodo}.json
  │      d. ResultWriter.write(result)
  │         → data/runs/export-result-{run_id}.json
  │
  └─ AppResult(exit_code=0, message="...", result=ExportacaoEspelhoResult)

Usuário
  "Espelho de Ponto exportado com sucesso para CELIO ..."
  "JSON: data/servidores/celio-proliciano-maioli/espelho-dezembro-2025.json"
```

## Transformação HTML → JSON

```
SigrhPageSnapshot.html
  │
  ▼ _EspelhoHTMLParser (html.parser.HTMLParser)
  │
  │  Detecção de linha:
  │  <tr id="frequenciaForm:listagemPontos:N:..."> → linha de dado SIGRH
  │
  │  Coleta de células (TD depth tracking):
  │  cells[0] = Data + Dia da Semana + Observação
  │  cells[1] = Horários Registrados (marcações)
  │  cells[2..11] = HR, HC, HE, HA, HH, Crédito, Débito, Saldo, CrédAcum, DNC
  │
  ▼ _sigrh_extract_row() → dict
  │
  ▼ EspelhoPontoParser._row_to_record() → RegistroDiaPonto
  │
  ▼ EspelhoPontoExport(registros=[...], servidor=..., periodo=...)
```

## Estrutura do JSON Gerado

```json
{
  "schema_version": 1,
  "run_id": "abc123",
  "captured_at": "2026-05-23T15:38:55+00:00",
  "status": "completed",
  "servidor": {
    "nome": "CELIO PROLICIANO MAIOLI",
    "identificador": "1534589",
    "texto_visivel": "..."
  },
  "periodo_referencia": "Dezembro/2025",
  "mensagens": [],
  "registros": [
    {
      "data": "2025-12-15",
      "dia_semana": "Segunda",
      "marcacoes": ["10:56", "19:01"],
      "ocorrencias": [],
      "observacoes": ["Servidor com designação remunerada."],
      "situacao": null,
      "textos_visiveis": [],
      "hr": "07:00",
      "hc": "01:05",
      "he": null,
      "ha": null,
      "hh": null,
      "credito": "01:05",
      "debito": null,
      "saldo_no_mes": "-06:55",
      "credito_acumulado": "00:00",
      "dnc": null
    }
  ],
  "fonte": {
    "tipo": "sigrh-espelho-ponto-visivel",
    "pagina": "/sigrh/frequencia/ponto_eletronico/consulta/...",
    "rotulos_visiveis": ["Espelho de Ponto"]
  }
}
```

## Localização dos Arquivos de Saída

```
data/
├── runs/                                           # resultados de operação
│   ├── export-result-{run_id}.json                #   ExportacaoEspelhoResult
│   ├── selection-result-{run_id}.json             #   SelecaoServidorResult
│   └── navigation-result-{run_id}.json            #   NavigationResult
└── servidores/                                     # espelhos por servidor
    ├── celio-proliciano-maioli/
    │   ├── espelho-dezembro-2025.json
    │   └── espelho-maio-2026.json
    └── jose-silva/
        └── espelho-abril-2026.json
```

## Tratamento de Erros

| Condição | Onde detectado | Ação |
|----------|---------------|------|
| Credenciais inválidas | `AuthenticationService` | `AppResult(exit_code=2)` |
| Anti-automação SIGRH | `SigrhBrowser` | `AppResult(exit_code=3)` |
| Sessão expirada | `EspelhoExportService` | `AppResult(exit_code=2)` |
| Servidor não encontrado | `ServerSelectionService` | `AppResult(exit_code=4)` |
| Página inválida (não é espelho) | `EspelhoPontoParser` | `AppResult(exit_code=3)` |
| Falha de escrita em disco | `ResultWriter` | `AppResult(exit_code=5/6)` |
| Espelho sem registros | `EspelhoPontoParser` | `AppResult(exit_code=0)` + status "empty" |
