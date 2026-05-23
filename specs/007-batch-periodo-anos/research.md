# Research: Período por Anos no Batch YAML

**Feature**: 007-batch-periodo-anos  
**Date**: 2026-05-23

---

## Decision 1: Representação de `anos` no BatchConfig

**Decision**: Campo `anos` adicionado ao `BatchConfig` como `list[int] | str | None`. O valor especial `"All"` é representado como string (não enum) para minimizar mudanças no loader YAML.  
**Rationale**: `yaml.safe_load` retorna listas Python diretamente; um `isinstance(anos, list)` é suficiente para distinguir lista de `"All"`. Enum adicionaria complexidade sem benefício de tipo em um loader que já valida entrada.  
**Alternatives considered**: `Literal["All"]` com `Union` — possível, mas requer `typing.get_args` para validação dinâmica e não simplifica o código de loader.

---

## Decision 2: Expansão de períodos — PeriodoExpander

**Decision**: Classe `PeriodoExpander` com método estático `expand(config, entry, today) -> list[tuple[int, int]]`. Recebe data "hoje" como parâmetro (injetável) para garantir determinismo nos testes.  
**Rationale**: Separar a lógica de expansão do `BatchService` permite testar exaustivamente todos os cenários (anos duplicados, meses futuros, "All") sem precisar de navegador.  
**Alternatives considered**: Expandir diretamente no `BatchService.run()` — mais simples mas mistura responsabilidades e dificulta testes isolados.

---

## Decision 3: Detecção de período de trabalho para `anos: All`

**Decision**: `AdmissaoDetector` tenta meses de forma regressiva a partir do mês corrente. Para cada mês recuado, chama `_run_single_espelho`; pára ao encontrar 3 falhas consecutivas (exit_code ≠ 0 e ≠ empty). Limite máximo de busca: 30 anos retroativos (2000–hoje).  
**Rationale**: O SIGRH não expõe endpoint de "data de admissão" diretamente — a única forma de saber qual é o primeiro mês disponível é tentar baixar. Parar em 3 falhas consecutivas evita buscar indefinidamente em meses antes da admissão.  
**Alternatives considered**:
- Scraping do campo "data de admissão" na tela de seleção de servidor — campo nem sempre visível, frágil a mudanças de layout.
- Binary search no período — reduz chamadas mas complexifica o algoritmo; para use cases reais (~20 anos = 240 meses), linear é aceitável.

---

## Decision 4: BatchEntryResult com mes/ano

**Decision**: Adicionar `mes: int | None = None` e `ano: int | None = None` ao `BatchEntryResult` como campos opcionais com defaults. `to_dict()` inclui esses campos somente quando não-None.  
**Rationale**: Com `anos`, o mesmo servidor aparece múltiplas vezes no relatório — diferenciar por período é essencial. Defaults opcionais mantêm compatibilidade com relatórios existentes.  
**Alternatives considered**: Incluir período no `nome` como string ("CELIO - 5/2026") — quebraria queries programáticas que usam `nome` como identificador.

---

## Decision 5: Precedência anos vs mes/ano

**Decision**: Se `anos` presente → ignora `mes`/`ano` do config e do entry; se `anos` ausente → comportamento idêntico à feature 006. Warning logado quando `anos` coexiste com `mes`/`ano`.  
**Rationale**: Usuários novos usam `anos`; usuários legados usam `mes`/`ano`. Precedência clara evita comportamento surpreendente. Warning no log é suficiente — não quebrar silenciosamente.

---

## Decision 6: Validação de `anos` no loader

**Decision**: Validar no `BatchConfigLoader.load()`: lista vazia → `BatchConfigError`; anos fora de [2000, 2100] → `BatchConfigError`; valor não-int na lista → `BatchConfigError`; string diferente de `"All"` (case-insensitive) → `BatchConfigError`.  
**Rationale**: O loader é a fronteira do sistema externo (arquivo YAML). Toda validação de entrada acontece aí, não nos dataclasses frozen.
