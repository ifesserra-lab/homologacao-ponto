---
name: "write-architecture"
description: "Document or update architecture for the project. Reads current code, generates or updates docs/architecture/ files in Portuguese."
compatibility: "Works on any Python project; reads src/ and tests/ for accurate documentation"
metadata:
  author: "local"
  source: ".agents/skills/write-architecture/SKILL.md"
---

## User Input

```text
$ARGUMENTS
```

If the user provided a specific scope (e.g. "document the parser layer", "update data flow"), focus on that.
If empty, generate or refresh all architecture documents.

## Outline

1. **Read current state**
   - List `src/` structure: `find src -name "*.py" | sort`
   - Read key files: `app.py`, `models/__init__.py`, service files, main infra adapters
   - Check what already exists in `docs/architecture/`

2. **Identify what to write or update**
   - `docs/architecture/overview.md` — component diagram (ASCII), module table, tech stack
   - `docs/architecture/layers.md` — directory tree per layer, responsibilities, contracts
   - `docs/architecture/data-flow.md` — ASCII flow diagram, JSON structure example, error table
   - Add new files only when the user explicitly asks for a specific topic

3. **Writing rules**
   - Language: **Portuguese (pt-BR)**
   - Diagrams: ASCII only — no Mermaid, no external renderers
   - Code examples: use actual class/method names from the current codebase
   - No speculation — only document what exists in code
   - Keep diagrams narrow (max 60 chars wide per box) for readability in editors
   - Use tables for module/field/error listings (more scannable than bullet lists)

4. **Structure each doc**
   - Start with one-sentence purpose statement
   - Main diagram or table first (most important content up top)
   - Sections use `##` headings (never deeper than `###` in architecture docs)
   - End with edge cases or constraints section when relevant

5. **Update `docs/architecture/` index** if a `README.md` exists there

6. **Report** which files were created or updated and one line explaining what changed.

## Quality Rules

- Every class/method name in docs MUST exist in current source — verify before writing
- Diagrams MUST reflect the actual call chain (check service constructors for real dependencies)
- Do NOT document planned features as current — if feature 005 is not implemented yet, say "planned"
- Keep docs short: if a section exceeds 60 lines, split into a separate file
