"""Loading of the store CSVs into validated domain models."""
from decimal import Decimal
from pathlib import Path

import pytest
from pydantic import ValidationError

from emporio.data.loader import load_active_promotions, load_categories, load_products

PRODUCT_HEADER = (
    "product_id,price_brl,name,category_id,description,stock_quantity,status,specs,created_at"
)
PROMOTION_HEADER = "promotion_id,product_id,discount_percent,description,is_active"


def write_table(directory: Path, table: str, header: str, *rows: str) -> None:
    """Writes a CSV named like the delivered files."""
    content = "\n".join([header, *rows]) + "\n"
    path = directory / f"desafio_tecnico_ai_eng - {table}.csv"
    _ = path.write_text(content, encoding="utf-8")


def test_real_products_load_with_unique_ids():
    ids = [product.id for product in load_products()]

    assert ids
    assert len(ids) == len(set(ids))


def test_inactive_promotions_are_not_loaded(tmp_path: Path):
    write_table(
        tmp_path,
        "promotions",
        PROMOTION_HEADER,
        "1,10,15,Black Friday,0",
        "2,20,10,Oferta Especial,1",
        "3,30,5,Aniversario,1",
    )

    promotions = load_active_promotions(tmp_path)

    assert [promotion.id for promotion in promotions] == [2, 3]


def test_products_are_built_from_csv_rows(tmp_path: Path):
    write_table(
        tmp_path,
        "products",
        PRODUCT_HEADER,
        '7,429.9,Test Nylon,5,"A, with comma",3,active,"{""strings"":""nylon""}",2021-03-15',
    )

    (product,) = load_products(tmp_path)

    assert product.id == 7
    assert product.price == Decimal("429.90")
    assert product.stock == 3
    assert product.description == "A, with comma"
    assert product.specs == {"strings": "nylon"}


def test_invalid_row_raises_validation_error(tmp_path: Path):
    write_table(
        tmp_path,
        "products",
        PRODUCT_HEADER,
        '7,-1,Bad price,5,desc,3,active,"{}",2021-03-15',
    )

    with pytest.raises(ValidationError):
        _ = load_products(tmp_path)


def test_missing_file_raises_file_not_found(tmp_path: Path):
    with pytest.raises(FileNotFoundError):
        _ = load_products(tmp_path)


def test_real_categories_include_those_without_products():
    category_ids = {category.id for category in load_categories()}
    product_category_ids = {product.category_id for product in load_products()}

    # Every product category exists, and at least one category has no products.
    assert product_category_ids < category_ids


def test_portuguese_color_name_is_unified_with_the_english_one():
    colors = {product.specs.get("color") for product in load_products()}

    assert "Preto" not in colors
    assert "Black" in colors


def test_distinct_colors_are_not_merged(tmp_path: Path):
    write_table(
        tmp_path,
        "products",
        PRODUCT_HEADER,
        '1,100.00,A,1,d,1,active,"{""color"":""Preto""}",2025-01-01',
        '2,100.00,B,1,d,1,active,"{""color"":""Wine Red""}",2025-01-01',
        '3,100.00,C,1,d,1,active,"{""color"":""Red""}",2025-01-01',
    )

    colors = [product.specs["color"] for product in load_products(tmp_path)]

    assert colors == ["Black", "Wine Red", "Red"]
