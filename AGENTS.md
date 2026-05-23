<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read
`specs/005-exportar-espelho-json/plan.md` and `.specify/memory/constitution.md`.
<!-- SPECKIT END -->

## Persona: Escrita Técnica

Ao documentar este projeto, siga estas regras:

- **Idioma**: português (pt-BR) para toda a prosa; nomes de código (classes, métodos, variáveis) permanecem em inglês
- **Público-alvo**: desenvolvedor técnico não familiarizado com este codebase específico
- **Tom**: direto, sem adjetivos de marketing; prefira exemplos concretos a descrições abstratas
- **Nomes exatos**: sempre cite a classe, método ou arquivo real — nunca diga "o módulo relevante"
- **Diagramas**: ASCII apenas (sem Mermaid, sem renderizadores externos)
- **Limitações**: documente edge cases e limitações conhecidas explicitamente
- **Sem especulação**: documente apenas o que existe no código; features planejadas são marcadas como "planejado"

### Regra: Backlog obrigatório após speckit-specify

**Toda execução de `speckit-specify` DEVE atualizar `docs/architecture/backlog.md`.**

Após criar ou atualizar uma spec, adicione ou atualize a linha correspondente na tabela do backlog:

```markdown
| NNN | `NNN-branch-name` | Título da feature | Draft | ✓/— | ✓/— |
```

Campos:
- **#** — número sequencial do diretório (ex: `005`)
- **Branch** — nome do diretório em `specs/` (ex: `005-exportar-espelho-json`)
- **Título** — linha `# Feature Specification: ...` do `spec.md`
- **Status** — campo `**Status**:` do `spec.md`
- **Plano** — ✓ se `plan.md` existe, — se ausente
- **Tasks** — ✓ se `tasks.md` existe, — se ausente

Arquivo: `docs/architecture/backlog.md`

### Documentação de Arquitetura

Arquivos vivem em `docs/architecture/`:

| Arquivo | Conteúdo |
|---------|----------|
| `overview.md` | Diagrama de componentes, tabela de módulos, tecnologias |
| `layers.md` | Árvore de diretórios por camada, responsabilidades, contratos |
| `data-flow.md` | Fluxo de dados ASCII, estrutura do JSON, tabela de erros |

Use `/write-architecture` para gerar ou atualizar esses documentos.
Use `/write-technical` para READMEs, runbooks, ADRs e docstrings.

### Comandos de Qualidade

```bash
.venv/bin/pytest -q                  # suite completa (deve passar)
.venv/bin/ruff check src tests       # lint
.venv/bin/ruff format --check src    # formatação
```
