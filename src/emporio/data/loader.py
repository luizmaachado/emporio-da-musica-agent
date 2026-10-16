"""Reads the store CSVs. The files are never modified; rules are applied in code."""
import csv
from pathlib import Path

from emporio.domain.catalog import Product
from emporio.domain.pricing import Promotion

DATA_DIR = Path(__file__).resolve().parents[3] / "data"
# The delivered CSV files are named "<prefix><table>.csv".
_FILE_PREFIX = "desafio_tecnico_ai_eng - "


def _read_rows(table: str, data_dir: Path) -> list[dict[str, str]]:
    with (data_dir / f"{_FILE_PREFIX}{table}.csv").open(newline="", encoding="utf-8") as file:
        return list(csv.DictReader(file))


def load_products(data_dir: Path = DATA_DIR) -> list[Product]:
    """Every product, validated; an invalid row raises `pydantic.ValidationError`."""
    return [Product.model_validate(row) for row in _read_rows("products", data_dir)]


def load_active_promotions(data_dir: Path = DATA_DIR) -> list[Promotion]:
    """Only promotions with `is_active = 1` apply; the rest are history."""
    promotions = (Promotion.model_validate(row) for row in _read_rows("promotions", data_dir))
    return [promotion for promotion in promotions if promotion.is_active]
