# Data Model: Exportar Tabela Completa do Espelho de Ponto por Servidor

**Feature**: 005-exportar-espelho-json | **Date**: 2026-05-23

## Entities

### RegistroDiaPonto (extended)

Representa um dia no espelho de ponto. Frozen dataclass.

| Campo | Tipo | Origem | Status |
|-------|------|--------|--------|
| `data` | `str` | célula data (DD/MM/YYYY → YYYY-MM-DD) | existente |
| `dia_semana` | `str \| None` | "Dia da Semana: X" na célula data | existente |
| `marcacoes` | `list[str]` | célula offset +1 (horários registrados) | existente |
| `ocorrencias` | `list[str]` | célula com "Ocorrência:" | existente |
| `observacoes` | `list[str]` | "Observação: X" na célula data | existente |
| `situacao` | `str \| None` | "Situação: X" na célula data | existente |
| `textos_visiveis` | `list[str]` | outros textos visíveis | existente |
| `hr` | `str \| None` | célula offset +2 | **novo** |
| `hc` | `str \| None` | célula offset +3 | **novo** |
| `he` | `str \| None` | célula offset +4 | **novo** |
| `ha` | `str \| None` | célula offset +5 | **novo** |
| `hh` | `str \| None` | célula offset +6 | **novo** |
| `credito` | `str \| None` | célula offset +7 | **novo** |
| `debito` | `str \| None` | célula offset +8 | **novo** |
| `saldo_no_mes` | `str \| None` | célula offset +9 | **novo** |
| `credito_acumulado` | `str \| None` | célula offset +10 | **novo** |
| `dnc` | `str \| None` | célula offset +11 | **novo** |

**Tipo dos valores**: string no formato HH:MM (ex: `"07:30"`, `"00:00"`, `"-08:00"`). `None` quando a célula está ausente ou contém apenas `"---"`.

**Invariantes**: `__post_init__` inalterado — apenas verifica que pelo menos um dos campos visíveis existentes (data, marcacoes, etc.) é não-vazio.

**to_dict()**: Todos os 17 campos incluídos. Novos campos com valor `None` aparecem como `null` no JSON — não são omitidos.

---

### EspelhoPontoExport (extended)

Agregado raiz do JSON exportado. Frozen dataclass.

**Campos existentes**: `run_id`, `captured_at`, `servidor`, `registros`, `periodo_referencia`, `mensagens`, `status`, `pagina`, `rotulos_visiveis`, `output_path` — **inalterados**.

**Propriedades novas**:

```python
@property
def output_subdir(self) -> str:
    return f"servidores/{_slug(self.servidor.nome)}"

@property
def output_filename(self) -> str:
    return f"espelho-{_periodo_slug(self.periodo_referencia, self.run_id)}.json"
```

**Helpers (module-level)**:

```python
def _slug(name: str) -> str:
    """ASCII slug from server name."""
    import unicodedata, re
    nfkd = unicodedata.normalize("NFD", name)
    ascii_only = "".join(c for c in nfkd if not unicodedata.combining(c))
    return re.sub(r"[^a-z0-9]+", "-", ascii_only.lower()).strip("-")

def _periodo_slug(periodo: str | None, run_id: str) -> str:
    if periodo:
        return periodo.lower().replace("/", "-")
    return run_id
```

---

### ResultWriter (updated)

```python
def write(self, result):
    subdir = getattr(result, "output_subdir", None)
    output_path = (
        self.output_dir / subdir / result.output_filename
        if subdir
        else self.output_dir / result.output_filename
    )
    self.output_dir.mkdir(parents=True, exist_ok=True)
    # if subdir exists, ensure it is created too
    output_path.parent.mkdir(parents=True, exist_ok=True)
    ...
```

---

## Storage Layout

```
data/
├── runs/                          # ExportacaoEspelhoResult, CrawlResult, etc. (unchanged)
│   ├── export-result-{run_id}.json
│   └── ...
└── servidores/                    # EspelhoPontoExport (new)
    ├── celio-proliciano-maioli/
    │   ├── espelho-dezembro-2025.json
    │   └── espelho-maio-2026.json
    └── jose-silva/
        └── espelho-abril-2026.json
```

---

## State Transitions

`EspelhoPontoExport.status`: `completed` | `empty` — unchanged.

No new state transitions introduced.
