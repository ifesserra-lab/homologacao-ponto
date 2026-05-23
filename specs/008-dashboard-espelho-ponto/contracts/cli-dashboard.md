# Contract: CLI `dashboard` Subcommand

**Feature**: 008-dashboard-espelho-ponto

## Command Signature

```
homologacao-ponto dashboard [--data-dir PATH] [--port PORT]
```

| Argument | Default | Description |
|----------|---------|-------------|
| `--data-dir` | `./data/runs` | Root directory containing `servidores/` subfolder |
| `--port` | `4321` | Port for the Astro dev server |

## Behaviour

1. Resolves `<data-dir>/servidores/` and passes its absolute path as
   `DATA_DIR` environment variable to the Astro process.
2. Runs `npm run dev -- --port <port>` inside the `dashboard/` directory.
3. Prints the local URL to stdout: `Dashboard em http://localhost:<port>`
4. Blocks until the user interrupts (Ctrl-C).

## Exit Codes

| Code | Meaning |
|------|---------|
| 0 | Server started successfully and user terminated cleanly |
| 1 | `dashboard/` directory not found (Astro not installed) |
| 2 | `npm run dev` exited with non-zero code |

## Error Messages

| Condition | Message (stderr) |
|-----------|-----------------|
| `dashboard/` not found | `Erro: pasta dashboard/ não encontrada. Execute 'npm install' em dashboard/.` |
| Port already in use | propagated from npm/Astro output |

## Test Contract

```python
# tests/integration/test_dashboard_cli.py
def test_dashboard_subcommand_exists(capsys):
    """dashboard subcommand must be registered in argparse."""
    result = subprocess.run(
        ["python", "-m", "homologacao_ponto.cli", "dashboard", "--help"],
        capture_output=True, text=True
    )
    assert result.returncode == 0
    assert "--data-dir" in result.stdout
    assert "--port" in result.stdout
```
