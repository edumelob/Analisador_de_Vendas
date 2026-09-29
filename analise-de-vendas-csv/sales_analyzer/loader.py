"""Leitura e validação do CSV de vendas."""
from __future__ import annotations

import csv
import io
import unicodedata
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path

from .models import Sale

REQUIRED = ("product", "quantity", "price")

# Nomes de coluna aceitos (já normalizados: minúsculas, sem acento, "_" no lugar de espaço).
ALIASES = {
    "produto": "product",
    "product": "product",
    "item": "product",
    "quantidade": "quantity",
    "quantity": "quantity",
    "qty": "quantity",
    "qtd": "quantity",
    "qtde": "quantity",
    "preco": "price",
    "price": "price",
    "preco_unitario": "price",
    "unit_price": "price",
    "data": "date",
    "date": "date",
    "categoria": "category",
    "category": "category",
}

COLUMN_LABELS = {
    "product": "produto",
    "quantity": "quantidade",
    "price": "preco",
}


class DataError(Exception):
    """Erro que impede a análise (arquivo ausente, colunas faltando, sem dados...)."""


@dataclass(frozen=True)
class RowError:
    line: int
    message: str


@dataclass
class LoadResult:
    sales: list[Sale] = field(default_factory=list)
    errors: list[RowError] = field(default_factory=list)


def _normalize_header(name: str) -> str:
    text = unicodedata.normalize("NFKD", name.strip().lower())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text.replace(" ", "_").replace("-", "_")


def parse_decimal(text: str) -> Decimal:
    """Converte '50.00', '50,00', 'R$ 1.234,56' ou '1,234.56' em Decimal.

    Regra: se houver vírgula e ponto, o ÚLTIMO dos dois é o separador decimal.
    Se houver só vírgula, ela é o separador decimal. Se houver só ponto, ele é o decimal.
    """
    cleaned = text.replace("R$", "").replace("\u00a0", "").replace(" ", "").strip()
    if not cleaned:
        raise ValueError("valor vazio")
    if "," in cleaned and "." in cleaned:
        if cleaned.rfind(",") > cleaned.rfind("."):
            cleaned = cleaned.replace(".", "").replace(",", ".")
        else:
            cleaned = cleaned.replace(",", "")
    elif "," in cleaned:
        cleaned = cleaned.replace(",", ".")
    try:
        value = Decimal(cleaned)
    except InvalidOperation:
        raise ValueError(f"número inválido: {text.strip()!r}") from None
    if not value.is_finite():
        raise ValueError(f"número inválido: {text.strip()!r}")
    return value


def parse_quantity(text: str) -> int:
    value = parse_decimal(text)
    if value != value.to_integral_value():
        raise ValueError(f"a quantidade deve ser um número inteiro: {text.strip()!r}")
    quantity = int(value)
    if quantity <= 0:
        raise ValueError(f"a quantidade deve ser maior que zero: {text.strip()!r}")
    return quantity


def parse_price(text: str) -> Decimal:
    value = parse_decimal(text)
    if value < 0:
        raise ValueError(f"o preço não pode ser negativo: {text.strip()!r}")
    return value


def parse_date(text: str) -> date:
    for fmt in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(text.strip(), fmt).date()
        except ValueError:
            continue
    raise ValueError(f"data inválida (use AAAA-MM-DD ou DD/MM/AAAA): {text.strip()!r}")


def _read_text(path: Path) -> str:
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        raise DataError(f"Arquivo não encontrado: {path}") from None
    except IsADirectoryError:
        raise DataError(f"O caminho é uma pasta, não um arquivo: {path}") from None
    except OSError as exc:
        raise DataError(f"Não foi possível ler o arquivo {path}: {exc.strerror or exc}") from None
    try:
        return raw.decode("utf-8-sig")
    except UnicodeDecodeError:
        # CSVs salvos pelo Excel em português costumam vir em ANSI (Windows-1252)
        return raw.decode("cp1252", errors="replace")


def _detect_delimiter(text: str) -> str:
    first_line = next((line for line in text.splitlines() if line.strip()), "")
    counts = {d: first_line.count(d) for d in (",", ";", "\t")}
    best = max(counts, key=counts.get)
    return best if counts[best] > 0 else ","


def load_sales(path: str | Path) -> LoadResult:
    """Lê o CSV. Linhas inválidas vão para `errors` e são ignoradas; problemas
    estruturais (arquivo ausente, colunas obrigatórias faltando) levantam DataError."""
    path = Path(path)
    text = _read_text(path)
    if not text.strip():
        raise DataError("O arquivo está vazio.")

    reader = csv.DictReader(io.StringIO(text, newline=""), delimiter=_detect_delimiter(text))
    headers = reader.fieldnames or []

    column_of: dict[str, str] = {}  # nome canônico -> nome original no arquivo
    for header in headers:
        canonical = ALIASES.get(_normalize_header(header))
        if canonical and canonical not in column_of:
            column_of[canonical] = header

    missing = [COLUMN_LABELS[c] for c in REQUIRED if c not in column_of]
    if missing:
        found = ", ".join(h.strip() for h in headers) or "nenhuma"
        raise DataError(
            f"Colunas obrigatórias ausentes: {', '.join(missing)}. Colunas encontradas: {found}."
        )

    def cell(row: dict, canonical: str) -> str:
        header = column_of.get(canonical)
        return (row.get(header) or "").strip() if header else ""

    result = LoadResult()
    for row in reader:
        line = reader.line_num
        if not any((value or "").strip() for key, value in row.items() if key is not None):
            continue  # linha em branco
        try:
            if row.get(None):
                raise ValueError("a linha tem mais colunas do que o cabeçalho")
            product = cell(row, "product")
            if not product:
                raise ValueError("produto vazio")
            date_text = cell(row, "date")
            result.sales.append(
                Sale(
                    product=product,
                    quantity=parse_quantity(cell(row, "quantity")),
                    price=parse_price(cell(row, "price")),
                    sold_on=parse_date(date_text) if date_text else None,
                    category=cell(row, "category") or None,
                )
            )
        except ValueError as exc:
            result.errors.append(RowError(line=line, message=str(exc)))
    return result
