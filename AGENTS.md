<!-- SPECKIT START -->
For additional context about technologies to be used, project structure,
shell commands, and other important information, read
`specs/010-dashboard-login-env/plan.md` and `.specify/memory/constitution.md`.
<!-- SPECKIT END -->

## Stack Tecnológica

Este projeto está migrando para app desktop com a seguinte stack:

| Camada | Tecnologia | Observação |
|--------|-----------|------------|
| Shell desktop | **Tauri 2** (Rust) | Substitui deploy web; empacota webview + sidecar |
| Frontend | **Vue 3** + Vite + TypeScript | Substitui Astro; `<script setup>` obrigatório |
| Estado global | **Pinia** | Store para dados do crawler e progresso |
| Crawler/ETL | **Node.js** + Playwright (TypeScript) | Substitui Python; executa como sidecar Tauri |
| IPC | `@tauri-apps/api/core` `invoke()` + `listen()` | Frontend ↔ Rust ↔ sidecar Node.js |
| Backend Rust | Tauri commands (`#[tauri::command]`) | Spawn sidecar, stream eventos ao frontend |

### Skills disponíveis para esta stack

| Skill | Trigger de uso |
|-------|----------------|
| `vue` | Escrever Vue SFCs, `defineProps`/`defineEmits`/`defineModel`, watchers |
| `vue-best-practices` | **Usar em toda tarefa Vue** — Composition API, `<script setup>`, TypeScript |
| `vue-pinia-best-practices` | Stores Pinia, estado global, reatividade |
| `tauri` | IPC, comandos Rust, configuração `tauri.conf.json`, plugins, segurança |
| `rust` | Código em `src-tauri/`, ownership, async Rust, Cargo |

### Comandos de desenvolvimento — Desktop (Tauri + Vue)

```bash
# Desenvolvimento (hot-reload Vue + Tauri)
npm run tauri dev

# Build de produção
npm run tauri build

# Apenas frontend Vue
npm run dev

# Type check Vue
vue-tsc --noEmit

# Testes unitários (Vitest)
npm run test
```

### Comandos de desenvolvimento — Crawler (Node.js)

```bash
# Executar crawler diretamente
npx ts-node crawler/index.ts

# Type check crawler
tsc --noEmit -p crawler/tsconfig.json

# Testes
npm run test:crawler
```

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
