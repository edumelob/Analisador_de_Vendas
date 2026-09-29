import json
from decimal import Decimal

import pytest

from sales_analyzer.analysis import summarize
from sales_analyzer.loader import load_sales
from sales_analyzer.report import format_brl, format_month, render_json, render_markdown, render_text


@pytest.mark.parametrize(
    "value, expected",
    [
        (Decimal("0"), "R$ 0,00"),
        (Decimal("5"), "R$ 5,00"),
        (Decimal("1234.5"), "R$ 1.234,50"),
        (Decimal("1234567.891"), "R$ 1.234.567,89"),
        (Decimal("-10.5"), "-R$ 10,50"),
        (Decimal("0.005"), "R$ 0,01"),
    ],
)
def test_format_brl(value, expected):
    assert format_brl(value) == expected


def test_format_month():
    assert format_month("2025-03") == "03/2025"


@pytest.fixture
def summary(write_csv):
    path = write_csv(
        """
        data,produto,categoria,quantidade,preco
        2025-01-03,Mouse,Periféricos,4,50.00
        2025-02-05,Monitor,Monitores,1,900.00
        """
    )
    return summarize(load_sales(path).sales)


def test_text_report_contents(summary):
    text = render_text(summary, top=5)
    assert "R$ 1.100,00" in text  # faturamento
    assert "R$ 550,00" in text  # ticket médio
    assert "Monitor" in text and "POR CATEGORIA" in text and "01/2025" in text
    assert "%" in text


def test_text_report_top_limits_rows(summary):
    assert "TOP 1 PRODUTOS" in render_text(summary, top=1)


def test_markdown_report(summary):
    md = render_markdown(summary)
    assert md.startswith("# Análise de Vendas")
    assert "| Produto | Qtd | Faturamento | % |" in md
    assert "| Mês | Qtd | Faturamento | % |" in md


def test_json_report_is_valid_and_exact(summary):
    data = json.loads(render_json(summary))
    assert data["revenue"] == "1100.00"
    assert data["average_ticket"] == "550.00"
    assert data["top_by_revenue"] == {"name": "Monitor", "quantity": 1, "revenue": "900.00"}
    assert [m["name"] for m in data["months"]] == ["2025-01", "2025-02"]
