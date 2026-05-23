from __future__ import annotations

import argparse
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
            result = app.run_espelho_ponto(servidor=args.servidor, mes=args.mes, ano=args.ano, siape=siape)
        elif args.servidor:
            result = app.run_espelho_ponto(servidor=args.servidor, siape=siape)
        else:
            result = app.run_espelho_ponto()
        stream = sys.stderr if result.exit_code else sys.stdout
        print(result.message, file=stream)
        return result.exit_code
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
