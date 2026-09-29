"""Cálculos de análise. Todo dinheiro usa Decimal (sem erros de arredondamento de float)."""
from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Callable, Sequence

from .models import Sale

NO_CATEGORY = "(sem categoria)"
CENTS = Decimal("0.01")


@dataclass(frozen=True)
class GroupStats:
    """Totais de um grupo (um produto, uma categoria ou um mês)."""

    name: str
    quantity: int
    revenue: Decimal


@dataclass(frozen=True)
class Summary:
    transactions: int
    items_sold: int
    revenue: Decimal
    average_ticket: Decimal
    top_by_quantity: GroupStats
    top_by_revenue: GroupStats
    products: tuple[GroupStats, ...]  # ordenados por receita (maior primeiro)
    categories: tuple[GroupStats, ...]  # vazio se o CSV não tem categoria
    months: tuple[GroupStats, ...]  # vazio se o CSV não tem data; nome no formato AAAA-MM


def _group(sales: Sequence[Sale], key: Callable[[Sale], str]) -> list[GroupStats]:
    quantity: dict[str, int] = defaultdict(int)
    revenue: dict[str, Decimal] = defaultdict(Decimal)
    for sale in sales:
        name = key(sale)
        quantity[name] += sale.quantity
        revenue[name] += sale.total
    return [GroupStats(name, quantity[name], revenue[name]) for name in quantity]


def by_revenue(groups: Sequence[GroupStats]) -> list[GroupStats]:
    """Maior receita primeiro; empate resolvido pelo nome (resultado sempre determinístico)."""
    return sorted(groups, key=lambda g: (-g.revenue, g.name))


def by_quantity(groups: Sequence[GroupStats]) -> list[GroupStats]:
    return sorted(groups, key=lambda g: (-g.quantity, g.name))


def summarize(sales: Sequence[Sale]) -> Summary:
    if not sales:
        raise ValueError("Não há vendas para analisar.")

    revenue = sum((s.total for s in sales), Decimal("0"))
    products = _group(sales, lambda s: s.product)

    categories: list[GroupStats] = []
    if any(s.category for s in sales):
        categories = by_revenue(_group(sales, lambda s: s.category or NO_CATEGORY))

    months: list[GroupStats] = []
    dated = [s for s in sales if s.sold_on is not None]
    if dated:
        months = sorted(_group(dated, lambda s: s.sold_on.strftime("%Y-%m")), key=lambda g: g.name)

    return Summary(
        transactions=len(sales),
        items_sold=sum(s.quantity for s in sales),
        revenue=revenue,
        average_ticket=(revenue / len(sales)).quantize(CENTS, rounding=ROUND_HALF_UP),
        top_by_quantity=by_quantity(products)[0],
        top_by_revenue=by_revenue(products)[0],
        products=tuple(by_revenue(products)),
        categories=tuple(categories),
        months=tuple(months),
    )
