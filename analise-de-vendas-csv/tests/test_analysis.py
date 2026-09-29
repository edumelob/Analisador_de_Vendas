from datetime import date
from decimal import Decimal

import pytest

from sales_analyzer.analysis import NO_CATEGORY, summarize
from sales_analyzer.models import Sale


def sale(product, qty, price, sold_on=None, category=None):
    return Sale(product, qty, Decimal(str(price)), sold_on, category)


ORIGINAL = [
    sale("Mouse", 4, "50.00"),
    sale("Teclado", 2, "150.00"),
    sale("Monitor", 1, "900.00"),
    sale("Mouse", 3, "50.00"),
    sale("Teclado", 1, "150.00"),
    sale("Fone", 5, "80.00"),
]


def test_original_dataset_numbers():
    s = summarize(ORIGINAL)
    assert s.transactions == 6
    assert s.items_sold == 16
    assert s.revenue == Decimal("2100.00")
    assert s.average_ticket == Decimal("350.00")
    assert (s.top_by_quantity.name, s.top_by_quantity.quantity) == ("Mouse", 7)
    assert s.top_by_revenue.name == "Monitor"
    assert [p.name for p in s.products] == ["Monitor", "Teclado", "Fone", "Mouse"]
    assert s.categories == () and s.months == ()


def test_money_is_exact_with_decimals():
    # Com float, 0.1 * 3 = 0.30000000000000004
    s = summarize([sale("A", 3, "0.10")])
    assert s.revenue == Decimal("0.30")


def test_average_ticket_rounds_half_up():
    s = summarize([sale("A", 1, "0.01"), sale("B", 1, "0.02")])  # 0.03 / 2 = 0.015
    assert s.average_ticket == Decimal("0.02")


def test_ties_are_deterministic():
    s = summarize([sale("Zeta", 1, "10"), sale("Alfa", 1, "10")])
    assert s.top_by_quantity.name == "Alfa"
    assert s.top_by_revenue.name == "Alfa"


def test_categories_and_months():
    s = summarize(
        [
            sale("A", 1, "10", date(2025, 2, 1), "X"),
            sale("B", 2, "10", date(2025, 1, 15), "X"),
            sale("C", 1, "5", date(2025, 1, 20), None),
        ]
    )
    assert [(c.name, c.revenue) for c in s.categories] == [("X", Decimal("30")), (NO_CATEGORY, Decimal("5"))]
    assert [(m.name, m.revenue) for m in s.months] == [("2025-01", Decimal("25")), ("2025-02", Decimal("10"))]


def test_empty_sales_raises():
    with pytest.raises(ValueError):
        summarize([])
