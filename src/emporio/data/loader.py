"""Reads the store CSVs. The files are never modified; rules are applied in code."""
import csv
from pathlib import Path

from emporio.domain.catalog import Category, Product
from emporio.domain.pricing import Promotion
from emporio.domain.text import normalize_text

DATA_DIR = Path(__file__).resolve().parents[3] / "data"
# The delivered CSV files are named "<prefix><table>.csv".
_FILE_PREFIX = "desafio_tecnico_ai_eng - "
# The data mixes Portuguese and English names for the same color. Only translations are merged:
# "Red" and "Wine Red" are different colors and stay apart.
_COLOR_ALIASES = {"preto": "Black"}


def _read_rows(table: str, data_dir: Path) -> list[dict[str, str]]:
    with (data_dir / f"{_FILE_PREFIX}{table}.csv").open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def _with_canonical_color(product: Product) -> Product:
    color = product.specs.get("color")
    canonical = _COLOR_ALIASES.get(normalize_text(color)) if color else None
    if canonical is None:
        return product
    return product.model_copy(update={"specs": product.specs | {"color": canonical}})


def load_products(data_dir: Path = DATA_DIR) -> list[Product]:
    """Every product, validated, with color names unified (`Preto` becomes `Black`).

    An invalid row raises `pydantic.ValidationError`.
    """
    rows = _read_rows("products", data_dir)
    return [_with_canonical_color(Product.model_validate(row)) for row in rows]


def load_categories(data_dir: Path = DATA_DIR) -> list[Category]:
    """Every category, including those with no products."""
    return [Category.model_validate(row) for row in _read_rows("categories", data_dir)]


def load_active_promotions(data_dir: Path = DATA_DIR) -> list[Promotion]:
    """Only promotions with `is_active = 1` apply; the rest are history."""
    promotions = (Promotion.model_validate(row) for row in _read_rows("promotions", data_dir))
    return [promotion for promotion in promotions if promotion.is_active]
