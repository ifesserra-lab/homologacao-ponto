# Research: Exportar Tabela Completa do Espelho de Ponto por Servidor

**Feature**: 005-exportar-espelho-json | **Date**: 2026-05-23

## R-001: Estrutura de células do SIGRH

**Decision**: Células em cada linha `frequenciaForm:listagemPontos:N:*` seguem ordem posicional fixa:

| offset | Coluna | Campo destino |
|--------|--------|--------------|
| +0 | Data (contém Dia da Semana + Observação embutidos) | `data`, `dia_semana`, `observacoes` |
| +1 | Horários Registrados | `marcacoes` |
| +2 | HR — Horas Regulares | `hr` |
| +3 | HC — Horas Complementares | `hc` |
| +4 | HE — Horas Extras | `he` |
| +5 | HA — Horas de Abono | `ha` |
| +6 | HH — Horas de Homologação | `hh` |
| +7 | Crédito | `credito` |
| +8 | Débito | `debito` |
| +9 | Saldo No Mês | `saldo_no_mes` |
| +10 | Crédito Acumulado | `credito_acumulado` |
| +11 | DNC — Dias Não Computados | `dnc` |

**Rationale**: Mapeamento confirmado por inspeção de HTML real do SIGRH (debug_espelho_live.html) e screenshot do usuário mostrando cabeçalhos na mesma ordem. Parser existente já coleta todas as células por profundidade de TD; só faltava ler os offsets além de +1.

**Fallback**: Se `date_idx + offset >= len(cells)`, campo retorna `None`. Colunas ausentes (ex: servidor PIT sem HR/HC) retornam `None`, não levantam exceção.

**Alternatives considered**: Detecção dinâmica por `<th>` — rejeitada porque cabeçalho fica em `<tr>` separado fora das linhas de dados; mapeamento posicional é consistente com abordagem atual do parser.

---

## R-002: Normalização de slug para nome de pasta

**Decision**: `unicodedata.normalize("NFD", name) → strip combining chars → lower() → sub("[^a-z0-9]+", "-") → strip("-")`.

Exemplos:
- `"CELIO PROLICIANO MAIOLI"` → `"celio-proliciano-maioli"`
- `"JOSÉ ARAÚJO"` → `"jose-araujo"`
- `"MARIA D'ALVA"` → `"maria-d-alva"`

**Rationale**: Slug ASCII puro, portável macOS/Linux, legível, resistente a colisão para nomes que diferem apenas em acentos. `unicodedata` é stdlib — zero dependências novas.

**Alternatives considered**: `unidecode` — rejeitado (dependência extra para normalização trivial). `lower()` sem NFD — rejeitado (acentos persistem, falha em FAT).

---

## R-003: Roteamento de caminho em ResultWriter

**Decision**: Adicionar `output_subdir: str | None` como property em `EspelhoPontoExport`. `ResultWriter.write()` resolve `output_dir / subdir / filename` quando subdir não-None, caso contrário `output_dir / filename` (comportamento atual preservado).

```
EspelhoPontoExport.output_subdir  → "servidores/celio-proliciano-maioli"
EspelhoPontoExport.output_filename → "espelho-dezembro-2025.json"
ExportacaoEspelhoResult.output_subdir → None  (campo ausente; getattr fallback)
```

**Rationale**: `ResultWriter` continua único gateway de escrita. Outros tipos de resultado não são afetados (`getattr(result, "output_subdir", None)` retorna None). `mkdir(parents=True, exist_ok=True)` já trata pastas aninhadas.

**Alternatives considered**: `EspelhoWriter` separado — rejeitado (duplica lógica). Caminho completo em `output_filename` — rejeitado (quebra `with_output_path` e mistura responsabilidades).

---

## R-004: Slug de período para nome de arquivo

**Decision**: `periodo_referencia.lower().replace("/", "-")` → `"dezembro-2025"` → filename `"espelho-dezembro-2025.json"`. Fallback quando `None`: `f"espelho-{run_id}.json"`.

**Rationale**: Legível; determinístico (re-run sobrescreve arquivo anterior); um arquivo por servidor/período conforme spec FR-005.
