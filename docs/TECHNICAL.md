# Technical Documentation — Espelhos de Ponto

## Overview

Desktop app (Tauri + Vue 3) that automates extraction of attendance records ("espelhos de ponto") from the IFES SIGRH system and visualizes them locally.

**Stack:**
| Layer | Technology |
|-------|-----------|
| Desktop shell | Tauri 2 (Rust) |
| Frontend | Vue 3 + Vite + TypeScript |
| State management | Pinia |
| Router | Vue Router 4 |
| Crawler | Node.js ESM + Playwright (headless Chromium) |
| Data | JSON files on disk |

---

## Repository Layout

```
homologacao_ponto/
├── desktop/                 # Tauri desktop app
│   ├── src/                 # Vue 3 frontend
│   │   ├── views/           # Page components (routes)
│   │   ├── components/      # Reusable UI components
│   │   ├── stores/          # Pinia state stores
│   │   ├── lib/             # Pure logic (repository, aggregation)
│   │   ├── types/           # TypeScript types
│   │   └── router/          # Vue Router config
│   ├── src-tauri/           # Rust backend
│   │   ├── src/lib.rs       # Tauri commands
│   │   └── tauri.conf.json  # App config
│   ├── src-crawler/         # Node.js crawler
│   │   ├── cli.js           # Entry point
│   │   ├── sigrh.js         # Playwright browser automation
│   │   ├── batch.js         # Batch loop
│   │   ├── parser.js        # HTML → JSON
│   │   └── writer.js        # JSON → disk
│   └── scripts/
│       └── bundle-crawler.mjs  # esbuild + pkg bundler
├── data/runs/servidores/    # Extracted espelho JSON files
├── servidores.yaml          # Servers to crawl + years
└── desktop/.env             # Credentials and config
```

---

## Configuration

### `desktop/.env`

```env
VITE_DATA_DIR=/absolute/path/to/data/runs/servidores

# SIGRH credentials
SIGRH_USERNAME=seu.login
SIGRH_PASSWORD=sua.senha

# Dashboard login (SHA-256 hashes)
VITE_USER_HASH=
VITE_PASSWORD_HASH=
```

`VITE_DATA_DIR` is read at Vite build time and injected into the frontend as `import.meta.env.VITE_DATA_DIR`. In dev mode it points to the repo's `data/runs/servidores`; in the installed app the Rust `resolve_data_dir` command looks for the folder relative to the executable or falls back to `app_local_data_dir`.

### `servidores.yaml`

```yaml
anos:
  - 2025
  - 2026
servidores:
  - nome: CELIO PROLICIANO MAIOLI
    siape: '1534589'
  - nome: GUSTAVO MAIA DE ALMEIDA
    siape: '2701647'
  # ...
```

Both files are editable from inside the app (Configurações tab) without touching the filesystem directly.

---

## Data Flow

```
User clicks "Executar Crawler"
        │
        ▼
Vue CrawlerView → invoke("run_crawler")
        │
        ▼
Rust lib.rs: run_crawler()
  ├── resolves node binary (Homebrew, /usr/local/bin, fallback "node")
  ├── in release builds: uses bundled crawler sidecar binary
  ├── spawns: node src-crawler/cli.js batch --file servidores.yaml --output-dir data/runs --env-file .env
  └── streams stdout/stderr → emits "crawler-log" Tauri event per line
        │
        ▼
cli.js → SigrhBrowser.login() → runBatch()
  ├── for each servidor × (mes, ano):
  │     browser.navigateToEspelho()
  │     browser.searchServer(nome, mes, ano, siape)
  │     browser.selectServer()
  │     html = browser.getHtml()
  │     espelho = parseEspelho(html)
  │     writeEspelho(espelho, outputDir)
  └── exits 0 on success, 1 if any failure

Process exits → Rust emits "crawler-done" event with exit code
        │
        ▼
Vue crawler.ts store: crawlerRefreshKey.value++ (when exitCode === 0)
        │
        ▼
All views watching crawlerRefreshKey → call store.load()
        │
        ▼
espelhoRepository.ts reads JSON files from VITE_DATA_DIR
        │
        ▼
Views re-render with fresh data
```

---

## Tauri Commands (Rust → `lib.rs`)

| Command | Description |
|---------|-------------|
| `resolve_data_dir` | Returns absolute path to `data/runs/servidores` |
| `run_crawler` | Spawns crawler process, streams logs via events |
| `get_config_paths` | Returns `{ env_path, servidores_path }` |
| `read_env_file` | Reads `desktop/.env` as string |
| `write_env_file(content)` | Writes `desktop/.env` |
| `read_servidores_file` | Reads `servidores.yaml` as string |
| `write_servidores_file(content)` | Writes `servidores.yaml` |

**Tauri Events (Rust → Frontend):**

| Event | Payload | When |
|-------|---------|------|
| `crawler-log` | `string` | Every stdout/stderr line from the crawler process |
| `crawler-done` | `number` | Process exit code when crawler finishes |

---

## Frontend Architecture

### Stores

**`stores/crawler.ts`**
- `running: boolean` — crawler active
- `logs: string[]` — log lines
- `exitCode: number | null`
- `progressDone / progressTotal` — parsed from `[batch:start]` / `[batch:progress]` protocol lines
- `progressPct: computed` — 0–100
- `crawlerRefreshKey: ref<number>` — module-level reactive; increments on success; views watch this to trigger reload without cross-store Pinia calls inside async event listeners

**`stores/servidores.ts`**
- `servidores: ServidorResume[]` — list of employees loaded from JSON
- `afastamentos: AfastamentoPeriodo[]` — absence records
- `loading / error`
- `load()` — calls `listServers()` + `loadAllAfastamentos()` in parallel

**`stores/auth.ts`** — Login state (SHA-256 hash comparison against `.env` hashes)

**`stores/theme.ts`** — `dark | light`, persisted to `localStorage`

### Views

| Route | View | Purpose |
|-------|------|---------|
| `/` | `ServidorListView` | Employee list with summary cards |
| `/servidor/:slug` | `ServidorDetailView` | Full history table + indicators tabs |
| `/servidor/:slug/:periodo` | `ServidorPeriodoView` | Single month detail |
| `/indicadores` | `IndicadoresView` | Global/detailed indicators dashboard |
| `/crawler` | `CrawlerView` | Run crawler, view logs, progress bar |
| `/config` | `ConfigView` | Edit `.env` and `servidores.yaml` |
| `/login` | `LoginView` | Auth form |

### Data Layer (`lib/`)

**`espelhoRepository.ts`**
- `listServers(dataDir)` — scans directory for slug folders, reads latest espelho per month, builds `ServidorResume[]`
- `serverDetail(slug, dataDir)` — full detail for one employee
- `monthDetail(slug, periodo, dataDir)` — single `RawEspelho`
- `loadAllAfastamentos(dataDir)` — collects absence records across all employees

**`lib/aggregation.ts`** — computes indicators (overtime balance, absence counts, anomalies) from `RawEspelho[]`

### Types (`types/dashboard.ts`)

Key types: `RawEspelho`, `ServidorResume`, `AfastamentoPeriodo`, `EspelhoDay`, `OcorrenciaEntry`

---

## Crawler Architecture (`src-crawler/`)

### `sigrh.js` — `SigrhBrowser`

Playwright wrapper around the SIGRH JSF web app.

| Method | Description |
|--------|-------------|
| `start()` | Launch browser (tries system Chrome/Edge first, falls back to bundled Chromium) |
| `login(user, pass)` | Fills login form, dismisses attendance popup |
| `navigateToEspelho()` | Direct URL navigation to `/consulta_ponto_eletronico.jsf` |
| `searchServer(nome, mes, ano, siape)` | Fills form, triggers autocomplete suggestion, clicks Buscar |
| `findServerRows()` | Returns list of result rows with `{ text, siape, hasSelect, row }` |
| `selectServer(rowData)` | Clicks "Selecionar Servidor" link |
| `getHtml()` | Returns full page HTML + injected `<div class="servidor">` and `<div class="periodo">` context |
| `close()` | Closes browser |

Browser launch strategy:
1. `chromium.launch({ channel: "chrome" })` — system Chrome
2. `chromium.launch({ channel: "msedge" })` — system Edge
3. `chromium.launch()` — bundled Playwright Chromium (downloads on first run)

### `batch.js` — `runBatch()`

Iterates `servidores × periodos` sequentially. Emits progress protocol lines to stdout:
- `[batch:start] total=N` — once at start
- `[batch:progress] done/total` — after each entry

### `cli.js` — Entry Point

```
node cli.js batch   --file servidores.yaml  [--output-dir path] [--env-file path] [--headed]
node cli.js espelho --servidor "NOME"        [--siape ID] [--mes M] [--ano Y]
```

`loadEnv()` searches `.env` in: explicit `--env-file`, dir next to binary (packaged), `../` relative to `__dirname`.

### `parser.js` — `parseEspelho()`

Parses SIGRH HTML into a structured `RawEspelho` JSON. Extracts:
- Server name, SIAPE, period (month/year)
- Day-by-day rows: date, entry/exit times, balance, occurrences
- Absence/afastamento entries

### `writer.js` — `writeEspelho()`

Writes to: `outputDir/servidores/<slug>/espelho-<month>-<year>.json`

Slug = server name lowercased, accents removed, spaces → hyphens.

---

## Build & Bundling

### Development

```bash
cd desktop
npm run tauri dev
```

Runs `npm run dev` (Vite on port 1420) + Rust Tauri shell concurrently. Crawler runs via `node src-crawler/cli.js` (not bundled binary).

### Production Build

```bash
cd desktop
npm run tauri build
```

The crawler is NOT automatically bundled into the binary — requires manual steps (see below).

### Crawler Bundling (`scripts/bundle-crawler.mjs`)

Because `pkg` can't statically analyze Playwright's dynamic `require(path.join(...))` calls, the build script:

1. **esbuild** bundles `src-crawler/cli.js` → `src-crawler/dist/crawler-bundle.cjs` with `platform: node`, `format: cjs`
2. **`playwright-pkg-shim` plugin** intercepts `playwright-core/lib/package.js` via `onLoad`, replacing dynamic `require()` with inlined version data
3. **Post-processing** regex-replaces remaining dynamic JSON requires (`package.json`, `browsers.json`, `api.json`) with inlined content
4. **`pkg`** packages the `.cjs` → platform binary with `--no-bytecode` (required: avoids `Invalid host defined options` from V8 bytecode compilation breaking `new Function()` in Playwright's `utilsBundle.js`)

```bash
cd desktop
node scripts/bundle-crawler.mjs
```

Output: `src-tauri/binaries/crawler-<target-triple>[.exe]`

In release builds, `resolve_crawler_sidecar()` in `lib.rs` finds this binary next to the app executable.

---

## Key Design Decisions

**`crawlerRefreshKey` module ref instead of cross-store call:**
`useServidoresStore()` called inside a Tauri async event listener runs outside Vue/Pinia setup context in some Pinia v3 versions, causing "getActivePinia() was called with no active Pinia" errors. The module-level `ref<number>` sidesteps this: stores and views watch it independently without requiring Pinia context at call time.

**Direct URL navigation instead of JSF menu clicks:**
SIGRH's portal menu uses JSF AJAX that changes visible content without changing the URL. Menu traversal via link-text clicking was unreliable across SIGRH versions. Navigating directly to the known JSF URL is stable.

**`--no-bytecode` in pkg:**
pkg's default V8 bytecode compilation breaks `new Function()` / `eval()` calls inside Playwright's `utilsBundle.js`. Adding `--no-bytecode --public-packages "*" --public` disables bytecode and makes modules transparent.

---

## Environment / Path Quirks

- Tauri's Rust process does not inherit the user's shell PATH on macOS. `lib.rs` explicitly prepends `/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin` to `PATH` before spawning the crawler.
- `resolve_node_bin()` tries hardcoded paths for common Node.js install locations before falling back to bare `"node"`.
- In dev mode (`#[cfg(debug_assertions)]`), `resolve_crawler_sidecar()` always returns `None`, so the Rust command always runs `node src-crawler/cli.js` directly.

---

## Adding a New Servidor

1. Edit `servidores.yaml` — add entry under `servidores:` with `nome` (exact SIGRH display name, uppercase) and `siape`
2. In app: Configurações tab → edit servidores, save
3. Run crawler — new JSON files appear under `data/runs/servidores/<slug>/`

## Adding a New Year

1. Edit `servidores.yaml` — add year to `anos:` list
2. Run crawler — extracts all 12 months for that year per servidor
