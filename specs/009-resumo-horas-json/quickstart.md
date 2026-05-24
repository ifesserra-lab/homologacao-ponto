# Quickstart: Resumo das Horas Apuradas no JSON

## Pré-requisitos

```bash
python -m pytest tests/ -x -q   # todos os testes existentes devem passar antes de começar
```

## Arquivos a modificar

| Arquivo | Mudança |
|---------|---------|
| `src/homologacao_ponto/models/espelho_ponto_export.py` | Adicionar `ResumoHorasApuradas`; atualizar `EspelhoPontoExport` |
| `src/homologacao_ponto/models/__init__.py` | Exportar `ResumoHorasApuradas` |
| `src/homologacao_ponto/infrastructure/espelho_ponto_parser.py` | Adicionar `_ResumoHTMLParser`; integrar ao `EspelhoPontoParser` |
| `tests/fixtures/sigrh_espelho_export_pages.py` | Adicionar `VALID_ESPELHO_WITH_RESUMO_HTML` |
| `dashboard/src/types/dashboard.ts` | Adicionar `ResumoHorasApuradas` e campo `resumo` em `RawEspelho` |
| `dashboard/src/lib/aggregation.ts` | Usar `resumo` quando disponível |
| `dashboard/src/pages/servidor/[slug]/[periodo].astro` | Passar `resumo` aos stats |

## Fluxo de desenvolvimento (TDD)

```
1. Escrever teste falhando: resumo capturado do HTML fixture
2. Implementar ResumoHorasApuradas + _ResumoHTMLParser
3. Green → refactor
4. Escrever teste falhando: to_dict() inclui campo resumo e schema_version=2
5. Atualizar EspelhoPontoExport
6. Green
7. Atualizar dashboard TypeScript + testes Vitest
```

## Verificação

```bash
# Python
python -m pytest tests/ -x -q

# Dashboard
cd dashboard && npm test

# Smoke: exportar um mês real e verificar campo resumo no JSON
python -m homologacao_ponto export --servidor "NOME" --mes "Maio/2026"
```
