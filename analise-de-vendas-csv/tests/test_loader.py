from datetime import date
from decimal import Decimal

import pytest

from sales_analyzer.loader import (
    DataError,
    load_sales,
    parse_date,
    parse_decimal,
    parse_price,
    parse_quantity,
)


@pytest.mark.parametrize(
    "text, expected",
    [
        ("50", "50"),
        ("50.00", "50.00"),
        ("50,00", "50.00"),
        ("1.234,56", "1234.56"),
        ("1,234.56", "1234.56"),
        ("R$ 1.234,56", "1234.56"),
        ("  7 ", "7"),
    ],
)
def test_parse_decimal_accepts_common_formats(text, expected):
    assert parse_decimal(text) == Decimal(expected)


@pytest.mark.parametrize("text", ["", "   ", "abc", "1.2.3", "NaN", "Infinity", "12,3,4"])
def test_parse_decimal_rejects_invalid(text):
    with pytest.raises(ValueError):
        parse_decimal(text)


def test_parse_quantity_rules():
    assert parse_quantity("4") == 4
    assert parse_quantity("4.0") == 4
    for bad in ("0", "-1", "2.5", "x", ""):
        with pytest.raises(ValueError):
            parse_quantity(bad)


def test_parse_price_rules():
    assert parse_price("0") == Decimal("0")
    with pytest.raises(ValueError):
        parse_price("-5")


def test_parse_date_formats():
    assert parse_date("2025-03-09") == date(2025, 3, 9)
    assert parse_date("09/03/2025") == date(2025, 3, 9)
    with pytest.raises(ValueError):
        parse_date("2025/03/09")
    with pytest.raises(ValueError):
        parse_date("31/02/2025")


def test_load_basic_file(write_csv):
    path = write_csv(
        """
        produto,quantidade,preco
        Mouse,4,50.00
        Teclado,2,150.00
        """
    )
    result = load_sales(path)
    assert result.errors == []
    assert [s.product for s in result.sales] == ["Mouse", "Teclado"]
    assert result.sales[0].total == Decimal("200.00")
    assert result.sales[0].sold_on is None and result.sales[0].category is None


def test_load_semicolon_and_decimal_comma(write_csv):
    path = write_csv(
        """
        Produto;Quantidade;Preço;Data;Categoria
        Mouse;4;50,00;05/01/2025;Periféricos
        Notebook;1;3.200,00;2025-01-06;Computadores
        """
    )
    result = load_sales(path)
    assert result.errors == []
    assert result.sales[1].price == Decimal("3200.00")
    assert result.sales[0].sold_on == date(2025, 1, 5)
    assert result.sales[0].category == "Periféricos"


def test_load_handles_bom_and_windows_encoding(write_csv):
    bom = write_csv("produto,quantidade,preco\nCafé,1,5\n", name="bom.csv", encoding="utf-8-sig")
    assert load_sales(bom).sales[0].product == "Café"

    ansi = write_csv("produto,quantidade,preco\nCafé,1,5\n", name="ansi.csv", encoding="cp1252")
    assert load_sales(ansi).sales[0].product == "Café"


def test_load_english_headers_and_reordered_columns(write_csv):
    path = write_csv(
        """
        price,qty,item
        10,3,Pen
        """
    )
    sale = load_sales(path).sales[0]
    assert (sale.product, sale.quantity, sale.price) == ("Pen", 3, Decimal("10"))


def test_invalid_rows_are_reported_with_line_numbers_and_skipped(write_csv):
    path = write_csv(
        """
        produto,quantidade,preco
        Mouse,4,50
        ,1,10
        Teclado,abc,150
        Monitor,0,900
        Fone,2,-1
        Cabo,1,5,extra
        Webcam,2,220

        """
    )
    result = load_sales(path)
    assert [s.product for s in result.sales] == ["Mouse", "Webcam"]
    assert [e.line for e in result.errors] == [3, 4, 5, 6, 7]
    assert "produto vazio" in result.errors[0].message


def test_missing_required_columns(write_csv):
    path = write_csv("produto,preco\nMouse,50\n")
    with pytest.raises(DataError) as exc:
        load_sales(path)
    assert "quantidade" in str(exc.value)


def test_file_problems(tmp_path, write_csv):
    with pytest.raises(DataError, match="não encontrado"):
        load_sales(tmp_path / "nao_existe.csv")
    with pytest.raises(DataError, match="pasta"):
        load_sales(tmp_path)
    with pytest.raises(DataError, match="vazio"):
        load_sales(write_csv("   \n", name="vazio.csv"))


def test_header_only_file_returns_no_sales(write_csv):
    result = load_sales(write_csv("produto,quantidade,preco\n"))
    assert result.sales == [] and result.errors == []
