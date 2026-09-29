"""Interface de linha de comando: python -m sales_analyzer [arquivo.csv]"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from . import __version__
from .analysis import summarize
from .loader import DataError, load_sales
from .report import render_json, render_markdown, render_text

DEFAULT_FILE = "data/vendas.csv"
MAX_WARNINGS_SHOWN = 10


def _positive_int(value: str) -> int:
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"{value!r} não é um número inteiro") from None
    if number < 1:
        raise argparse.ArgumentTypeError("o valor deve ser pelo menos 1")
    return number


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="sales_analyzer",
        description="Analisa um CSV de vendas: faturamento, ticket médio, ranking de produtos e mais.",
    )
    parser.add_argument("csv_file", nargs="?", default=DEFAULT_FILE, help=f"arquivo CSV (padrão: {DEFAULT_FILE})")
    parser.add_argument("--top", type=_positive_int, default=5, metavar="N", help="quantos produtos mostrar no ranking (padrão: 5)")
    parser.add_argument("--export-json", metavar="ARQUIVO", help="salva o resumo em JSON")
    parser.add_argument("--export-md", metavar="ARQUIVO", help="salva o relatório em Markdown")
    parser.add_argument("--strict", action="store_true", help="falha se houver qualquer linha inválida (em vez de ignorá-las)")
    parser.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    return parser


def _write(path: str, content: str) -> None:
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(content, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    # Evita UnicodeEncodeError em terminais com codificação limitada
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except (AttributeError, ValueError, OSError):
            pass

    args = build_parser().parse_args(argv)

    try:
        result = load_sales(args.csv_file)
    except DataError as exc:
        print(f"Erro: {exc}", file=sys.stderr)
        return 1

    if result.errors:
        shown = result.errors[:MAX_WARNINGS_SHOWN]
        label = "Erro" if args.strict else "Aviso"
        for err in shown:
            print(f"{label}: linha {err.line}: {err.message}", file=sys.stderr)
        hidden = len(result.errors) - len(shown)
        if hidden > 0:
            print(f"{label}: ... e mais {hidden} linha(s) com problema.", file=sys.stderr)
        if args.strict:
            print(f"Erro: {len(result.errors)} linha(s) inválida(s) (modo --strict).", file=sys.stderr)
            return 1
        print(f"Aviso: {len(result.errors)} linha(s) ignorada(s); {len(result.sales)} válida(s).", file=sys.stderr)

    if not result.sales:
        print("Erro: nenhuma venda válida para analisar.", file=sys.stderr)
        return 1

    summary = summarize(result.sales)
    print(render_text(summary, top=args.top), end="")

    try:
        if args.export_json:
            _write(args.export_json, render_json(summary))
            print(f"\nJSON salvo em: {args.export_json}")
        if args.export_md:
            _write(args.export_md, render_markdown(summary, top=args.top))
            print(f"Markdown salvo em: {args.export_md}")
    except OSError as exc:
        print(f"Erro ao salvar o arquivo: {exc.strerror or exc}", file=sys.stderr)
        return 1
    return 0
