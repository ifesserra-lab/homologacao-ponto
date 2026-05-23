# Quickstart: Dashboard de Espelhos de Ponto

**Feature**: 008-dashboard-espelho-ponto

## Prerequisites

- Node.js 18+ (`node --version`)
- npm 9+ (`npm --version`)
- Espelhos exportados em `data/runs/servidores/`

## Setup (first time)

```bash
cd dashboard
npm install
```

## Run

```bash
# via CLI (recommended)
homologacao-ponto dashboard

# or directly
cd dashboard && npm run dev
```

Open: http://localhost:4321

## Run with custom data dir or port

```bash
homologacao-ponto dashboard --data-dir ./data/runs --port 4321
```

## Tests

```bash
# Astro/TypeScript unit tests
cd dashboard && npm run test

# Python CLI test
pytest tests/integration/test_dashboard_cli.py -v
```

## Build static site (optional)

```bash
cd dashboard && npm run build
# Output in dashboard/dist/
```
