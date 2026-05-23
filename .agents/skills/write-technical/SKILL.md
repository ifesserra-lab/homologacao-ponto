---
name: "write-technical"
description: "Write or update technical documentation: READMEs, runbooks, spec supplements, ADRs, or inline code explanations. Output in Portuguese."
compatibility: "Works on any project with .specify/ structure or standalone"
metadata:
  author: "local"
  source: ".agents/skills/write-technical/SKILL.md"
---

## User Input

```text
$ARGUMENTS
```

Expected forms:
- `"README"` — generate or update root README.md
- `"runbook para espelho-ponto"` — operational runbook for a feature
- `"ADR: troca do parser HTML"` — Architecture Decision Record
- `"docstring para EspelhoPontoParser"` — inline code documentation
- Empty — ask the user which document type they need

## Document Types

### README
Target audience: developer setting up the project for the first time.

Required sections:
1. **O que é** (one paragraph, plain language)
2. **Pré-requisitos** (Python version, env vars, external dependencies)
3. **Instalação**
4. **Uso** (concrete CLI examples with real flags)
5. **Testes** (exact command to run the full suite)
6. **Estrutura do projeto** (top-level directory tree only, one-line description per item)

### Runbook
Target audience: operator running the tool in production.

Required sections:
1. **Objetivo** (what the runbook covers)
2. **Pré-condições** (what must be true before starting)
3. **Passo a passo** (numbered steps; include exact commands)
4. **Verificação** (how to confirm success)
5. **Solução de problemas** (table: symptom → cause → fix)

### ADR (Architecture Decision Record)
Required sections:
1. **Contexto** (what problem forced this decision)
2. **Decisão** (what was chosen, one clear sentence)
3. **Alternativas consideradas** (table: option, pros, cons)
4. **Consequências** (what becomes easier, what becomes harder)
5. **Status**: Proposta | Aceita | Substituída por [link]

### Docstrings
- One-line summary only — no multi-paragraph blocks
- Document the WHY (non-obvious constraint or invariant), not the WHAT
- Use reStructuredText style only when the project already uses it

## Writing Rules

- Language: **Portuguese (pt-BR)** for all prose
- Code blocks and identifiers: keep original language (English variable names, etc.)
- Tone: technical, direct, no marketing language
- No placeholder sections — only write sections with real content
- No "TODO" or "WIP" text in deliverables
- Max line length in prose: 100 chars (for git diff readability)
- Use `>` blockquote for warnings or critical notes only

## Persona

Write as a senior software engineer documenting their own system:
- Assume the reader is technical but unfamiliar with this specific codebase
- Prefer concrete examples over abstract descriptions
- Name the exact command, class, or file — never say "the relevant module"
- Acknowledge limitations and known edge cases explicitly

## Process

1. Read the target file or code to document (never guess contents)
2. Draft the document following the appropriate template above
3. Verify all code references exist in source before writing
4. Write the file to the appropriate path:
   - README → project root `README.md`
   - Runbooks → `docs/runbooks/{topic}.md`
   - ADRs → `docs/decisions/ADR-{NNN}-{slug}.md`
   - Architecture → `docs/architecture/{topic}.md`
5. Report the file path and a one-line summary of what was written
