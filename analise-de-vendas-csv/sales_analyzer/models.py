from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal


@dataclass(frozen=True)
class Sale:
    """Uma linha do CSV: uma venda de um produto."""

    product: str
    quantity: int
    price: Decimal
    sold_on: date | None = None
    category: str | None = None

    @property
    def total(self) -> Decimal:
        return self.price * self.quantity
