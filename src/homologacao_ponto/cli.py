from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

from homologacao_ponto.app import create_app


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="homologacao-ponto")
    subcommands = parser.add_subparsers(dest="command", required=True)
    crawl = subcommands.add_parser("crawl")
    crawl.add_argument("--output-dir", default="./data/runs")
    crawl.add_argument("--env-file", default=".env")
    crawl.add_argument("--headed", action="store_true")
    espelho = subcommands.add_parser("espelho-ponto")
    espelho.add_argument("--output-dir", default="./data/runs")
    espelho.add_argument("--env-file", default=".env")
    espelho.add_argument("--headed", action="store_true")
    espelho.add_argument("--servidor")
    espelho.add_argument("--mes", type=int, choices=range(1, 13), metavar="{1..12}")
    espelho.add_argument("--ano", type=int)
    espelho.add_argument("--siape")
    batch = subcommands.add_parser("batch")
    batch.add_argument(
        "--file",
        required=True,
        help="Caminho para arquivo YAML com lista de servidores",
    )
    batch.add_argument("--output-dir", default="./data/runs")
    batch.add_argument("--env-file", default=".env")
    batch.add_argument("--mes", type=int, choices=range(1, 13), metavar="{1..12}")
    batch.add_argument("--ano", type=int)
    dashboard = subcommands.add_parser("dashboard", help="Inicia dashboard local de espelhos de ponto")
    dashboard.add_argument("--data-dir", default="./data/runs", help="Diretório raiz com pasta servidores/")
    dashboard.add_argument("--port", type=int, default=4321, help="Porta do servidor Astro (padrão: 4321)")
    dashboard.add_argument("--dashboard-dir", default=None, help="Caminho para pasta dashboard/ (padrão: auto-detectado)")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command == "crawl":
        app = create_app(
            output_dir=Path(args.output_dir),
            env_file=Path(args.env_file),
            headed=args.headed,
        )
        result = app.run()
        stream = sys.stderr if result.exit_code else sys.stdout
        print(result.message, file=stream)
        return result.exit_code
    if args.command == "espelho-ponto":
        app = create_app(
            output_dir=Path(args.output_dir),
            env_file=Path(args.env_file),
            headed=args.headed,
        )
        siape = getattr(args, "siape", None)
        if args.servidor and (args.mes is not None or args.ano is not None):
            result = app.run_espelho_ponto(
                servidor=args.servidor, mes=args.mes, ano=args.ano, siape=siape
            )
        elif args.servidor:
            result = app.run_espelho_ponto(servidor=args.servidor, siape=siape)
        else:
            result = app.run_espelho_ponto()
        stream = sys.stderr if result.exit_code else sys.stdout
        print(result.message, file=stream)
        return result.exit_code
    if args.command == "batch":
        from pathlib import Path as _Path
        from homologacao_ponto.models.batch_config import (
            BatchConfig,
            BatchConfigLoader,
            BatchConfigError,
        )

        try:
            config = BatchConfigLoader.load(_Path(args.file))
            if args.mes:
                config = BatchConfig(
                    servidores=config.servidores, mes=args.mes, ano=config.ano
                )
            if args.ano:
                config = BatchConfig(
                    servidores=config.servidores, mes=config.mes, ano=args.ano
                )
        except BatchConfigError as exc:
            print(f"Erro no arquivo YAML: {exc}", file=__import__("sys").stderr)
            return 1
        app = create_app(output_dir=args.output_dir, env_file=args.env_file)
        result = app.run_batch(config)
        print(result.message)
        return result.exit_code
    if args.command == "dashboard":
        dashboard_dir = Path(args.dashboard_dir) if args.dashboard_dir else Path(__file__).parent.parent.parent.parent / "dashboard"
        if not dashboard_dir.exists():
            print(f"Erro: pasta dashboard/ não encontrada em {dashboard_dir}. Execute 'npm install' em dashboard/.", file=sys.stderr)
            return 1
        data_dir = str(Path(args.data_dir).resolve() / "servidores")
        env = {**os.environ, "DATA_DIR": data_dir}
        print(f"Dashboard em http://localhost:{args.port}")
        result = subprocess.run(
            ["npm", "run", "dev", "--", "--port", str(args.port)],
            cwd=dashboard_dir,
            env=env,
        )
        return 0 if result.returncode == 0 else 2
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
