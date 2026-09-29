"""Formatação do relatório (texto no terminal, Markdown e JSON)."""
from __future__ import annotations

import json
from decimal import ROUND_HALF_UP, Decimal

from .analysis import CENTS, GroupStats, Summary

BAR_WIDTH = 20


def format_brl(value: Decimal) -> str:
    """Decimal('1234.5') -> 'R$ 1.234,50'."""
    q = value.quantize(CENTS, rounding=ROUND_HALF_UP)
    sign = "-" if q < 0 else ""
    integer, cents = f"{abs(q):.2f}".split(".")
    return f"{sign}R$ {int(integer):,}".replace(",", ".") + f",{cents}"


def format_month(key: str) -> str:
    year, month = key.split("-")
    return f"{month}/{year}"


def _percent(part: Decimal, total: Decimal) -> str:
    if total == 0:
        return "0,0%"
    value = (part * 100 / total).quantize(Decimal("0.1"), rounding=ROUND_HALF_UP)
    return f"{value}%".replace(".", ",")


def _bar(part: Decimal, biggest: Decimal) -> str:
    if biggest <= 0:
        return ""
    return "#" * max(1, round(BAR_WIDTH * part / biggest)) if part > 0 else ""


def _table(rows: list[list[str]], headers: list[str], right: set[int]) -> list[str]:
    widths = [max([len(headers[i])] + [len(r[i]) for r in rows]) for i in range(len(headers))]

    def fmt(cells: list[str]) -> str:
        parts = [c.rjust(widths[i]) if i in right else c.ljust(widths[i]) for i, c in enumerate(cells)]
        return "  ".join(parts).rstrip()

    return [fmt(headers), "  ".join("-" * w for w in widths), *(fmt(r) for r in rows)]


def _group_rows(groups: list[GroupStats], total: Decimal, label=lambda n: n, bars: bool = False) -> list[list[str]]:
    biggest = max((g.revenue for g in groups), default=Decimal(0))
    rows = []
    for g in groups:
        row = [label(g.name), str(g.quantity), format_brl(g.revenue), _percent(g.revenue, total)]
        if bars:
            row.append(_bar(g.revenue, biggest))
        rows.append(row)
    return rows


def render_text(summary: Summary, top: int = 5) -> str:
    def line(label: str, value: str) -> str:
        return f"{label:<22}: {value}"

    out = [
        "=" * 60,
        " ANÁLISE DE VENDAS",
        "=" * 60,
        line("Transações (linhas)", str(summary.transactions)),
        line("Itens vendidos", str(summary.items_sold)),
        line("Faturamento total", format_brl(summary.revenue)),
        line("Ticket médio", format_brl(summary.average_ticket)),
        line("Mais vendido (qtd)", f"{summary.top_by_quantity.name} ({summary.top_by_quantity.quantity} un.)"),
        line("Maior faturamento", f"{summary.top_by_revenue.name} ({format_brl(summary.top_by_revenue.revenue)})"),
        "",
        f"TOP {min(top, len(summary.products))} PRODUTOS POR FATURAMENTO",
    ]
    out += _table(
        _group_rows(list(summary.products[:top]), summary.revenue, bars=True),
        ["Produto", "Qtd", "Faturamento", "%", ""],
        right={1, 2, 3},
    )
    if summary.categories:
        out += ["", "POR CATEGORIA"]
        out += _table(
            _group_rows(list(summary.categories), summary.revenue),
            ["Categoria", "Qtd", "Faturamento", "%"],
            right={1, 2, 3},
        )
    if summary.months:
        out += ["", "POR MÊS"]
        out += _table(
            _group_rows(list(summary.months), summary.revenue, label=format_month),
            ["Mês", "Qtd", "Faturamento", "%"],
            right={1, 2, 3},
        )
    return "\n".join(out) + "\n"


def render_markdown(summary: Summary, top: int = 5) -> str:
    def table(title: str, first_column: str, groups, label=lambda n: n) -> list[str]:
        lines = ["", f"## {title}", "", f"| {first_column} | Qtd | Faturamento | % |", "|---|---:|---:|---:|"]
        for g in groups:
            lines.append(
                f"| {label(g.name)} | {g.quantity} | {format_brl(g.revenue)} | {_percent(g.revenue, summary.revenue)} |"
            )
        return lines

    out = [
        "# Análise de Vendas",
        "",
        f"- **Transações (linhas):** {summary.transactions}",
        f"- **Itens vendidos:** {summary.items_sold}",
        f"- **Faturamento total:** {format_brl(summary.revenue)}",
        f"- **Ticket médio:** {format_brl(summary.average_ticket)}",
        f"- **Mais vendido (quantidade):** {summary.top_by_quantity.name} ({summary.top_by_quantity.quantity} un.)",
        f"- **Maior faturamento:** {summary.top_by_revenue.name} ({format_brl(summary.top_by_revenue.revenue)})",
    ]
    out += table(f"Top {min(top, len(summary.products))} produtos por faturamento", "Produto", summary.products[:top])
    if summary.categories:
        out += table("Por categoria", "Categoria", summary.categories)
    if summary.months:
        out += table("Por mês", "Mês", summary.months, label=format_month)
    return "\n".join(out) + "\n"


def _money(value: Decimal) -> str:
    return str(value.quantize(CENTS, rounding=ROUND_HALF_UP))


def _group_dict(g: GroupStats) -> dict:
    return {"name": g.name, "quantity": g.quantity, "revenue": _money(g.revenue)}


def to_dict(summary: Summary) -> dict:
    return {
        "transactions": summary.transactions,
        "items_sold": summary.items_sold,
        "revenue": _money(summary.revenue),
        "average_ticket": _money(summary.average_ticket),
        "top_by_quantity": _group_dict(summary.top_by_quantity),
        "top_by_revenue": _group_dict(summary.top_by_revenue),
        "products": [_group_dict(g) for g in summary.products],
        "categories": [_group_dict(g) for g in summary.categories],
        "months": [_group_dict(g) for g in summary.months],
    }


def render_json(summary: Summary) -> str:
    return json.dumps(to_dict(summary), ensure_ascii=False, indent=2) + "\n"
