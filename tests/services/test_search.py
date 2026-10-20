"""Product search and category listing."""
from decimal import Decimal

import pytest

from emporio.data.loader import load_active_promotions, load_categories, load_products
from emporio.domain.catalog import Availability, Category, Product
from emporio.domain.errors import DomainError, ErrorCode
from emporio.domain.pricing import Promotion
from emporio.services.search import (
    ProductFilters,
    ProductSearchService,
    SortOrder,
    StringType,
)
from tests.factories import make_category, make_product, make_promotion

CATEGORIES = [make_category(1, "Guitarras"), make_category(2, "Violões"), make_category(3, "Sopros")]


def search_service(
    products: list[Product],
    promotions: list[Promotion] | None = None,
    categories: list[Category] | None = None,
) -> ProductSearchService:
    return ProductSearchService(products, categories or CATEGORIES, promotions or [])


def found_ids(service: ProductSearchService, **filters: object) -> list[int]:
    return [item.product.id for item in service.search(ProductFilters.model_validate(filters)).items]


@pytest.fixture(scope="module")
def store_search() -> ProductSearchService:
    return ProductSearchService(load_products(), load_categories(), load_active_promotions())


# Availability


def test_only_available_products_are_returned_by_default():
    service = search_service(
        [
            make_product(1),
            make_product(2, stock=0),
            make_product(3, status="discontinued"),
            make_product(4, status="coming_soon"),
        ]
    )

    assert found_ids(service) == [1]


def test_include_unavailable_returns_everything_with_the_right_label():
    service = search_service(
        [make_product(1), make_product(2, stock=0), make_product(3, status="discontinued")]
    )

    result = service.search(ProductFilters(include_unavailable=True))

    labels = {item.product.id: item.product.availability for item in result.items}
    assert labels == {
        1: Availability.AVAILABLE,
        2: Availability.OUT_OF_STOCK,
        3: Availability.UNAVAILABLE,
    }


# Text


def test_query_requires_every_word():
    service = search_service(
        [
            make_product(1, name="Yamaha acoustic"),
            make_product(2, name="Yamaha electric"),
            make_product(3, name="Fender acoustic"),
        ]
    )

    assert found_ids(service, query="yamaha acoustic") == [1]


def test_query_ignores_case_and_accents():
    service = search_service([make_product(1, description="Violão clássico")])

    assert found_ids(service, query="VIOLAO Classico") == [1]


def test_query_matches_name_description_and_category_name():
    service = search_service(
        [
            make_product(1, name="Tagima", category_id=1),
            make_product(2, name="Other", description="Great for jazz", category_id=1),
            make_product(3, name="Other", category_id=3),
        ]
    )

    assert found_ids(service, query="tagima") == [1]
    assert found_ids(service, query="jazz") == [2]
    assert found_ids(service, query="sopros") == [3]


def test_empty_query_does_not_filter():
    service = search_service([make_product(1), make_product(2)])

    assert found_ids(service, query="  ") == [1, 2]


def test_query_without_match_is_an_empty_result():
    service = search_service([make_product(1)])

    assert found_ids(service, query="trombone") == []


# Price


def test_price_filters_use_the_final_price_and_are_inclusive():
    service = search_service(
        [make_product(1, "100.00"), make_product(2, "200.00"), make_product(3, "300.00")],
        [make_promotion("50", product_id=3)],
    )

    assert found_ids(service, min_price=Decimal(100), max_price=Decimal(150)) == [1, 3]
    assert found_ids(service, min_price=Decimal(200)) == [2]
    assert found_ids(service, max_price=Decimal(150)) == [1, 3]


def test_equal_min_and_max_price_is_a_valid_range():
    service = search_service([make_product(1, "100.00"), make_product(2, "200.00")])

    assert found_ids(service, min_price=Decimal(100), max_price=Decimal(100)) == [1]


def test_min_price_above_max_price_is_refused():
    service = search_service([make_product(1)])

    with pytest.raises(DomainError) as error:
        _ = service.search(ProductFilters(min_price=Decimal(10), max_price=Decimal(5)))

    assert error.value.code is ErrorCode.INVALID_PRICE_RANGE


# Attributes


def test_string_type_ignores_products_where_strings_is_a_count():
    service = search_service(
        [
            make_product(1, specs={"strings": "nylon"}),
            make_product(2, specs={"strings": "steel"}),
            make_product(3, specs={"strings": "6"}),
            make_product(4),
        ]
    )

    assert found_ids(service, string_type=StringType.NYLON) == [1]
    assert found_ids(service, string_type=StringType.STEEL) == [2]


def test_color_is_an_exact_match_ignoring_case():
    service = search_service(
        [
            make_product(1, specs={"color": "Red"}),
            make_product(2, specs={"color": "Wine Red"}),
            make_product(3),
        ]
    )

    assert found_ids(service, color="red") == [1]
    assert found_ids(service, color="WINE RED") == [2]


def test_electronics_filter_ignores_products_without_the_spec():
    service = search_service(
        [
            make_product(1, specs={"electronics": "yes"}),
            make_product(2, specs={"electronics": "no"}),
            make_product(3),
        ]
    )

    assert found_ids(service, electronics=True) == [1]
    assert found_ids(service, electronics=False) == [2]


# Category


def test_category_filter_keeps_only_that_category():
    service = search_service([make_product(1, category_id=1), make_product(2, category_id=2)])

    assert found_ids(service, category_id=2) == [2]


def test_unknown_category_is_refused():
    service = search_service([make_product(1)])

    with pytest.raises(DomainError) as error:
        _ = service.search(ProductFilters(category_id=99))

    assert error.value.code is ErrorCode.UNKNOWN_CATEGORY


def test_category_without_products_is_an_empty_result():
    service = search_service([make_product(1, category_id=1)])

    assert found_ids(service, category_id=3) == []


# Sorting


def test_results_are_sorted_by_final_price_then_name_by_default():
    service = search_service(
        [
            make_product(1, "200.00", name="B"),
            make_product(2, "100.00", name="Z"),
            make_product(3, "100.00", name="A"),
            make_product(4, "400.00", name="C"),
        ],
        [make_promotion("50", product_id=4)],
    )

    assert found_ids(service) == [3, 2, 1, 4]


def test_results_can_be_sorted_by_descending_price():
    service = search_service(
        [make_product(1, "100.00"), make_product(2, "300.00"), make_product(3, "200.00")]
    )

    assert found_ids(service, sort=SortOrder.PRICE_DESC) == [2, 3, 1]


def test_equal_prices_are_ordered_by_name_in_both_directions():
    service = search_service(
        [make_product(1, name="B"), make_product(2, name="A"), make_product(3, name="C")]
    )

    assert found_ids(service) == [2, 1, 3]
    assert found_ids(service, sort=SortOrder.PRICE_DESC) == [2, 1, 3]


# Items


def test_each_item_carries_its_price_breakdown():
    service = search_service([make_product(1, "250.00")], [make_promotion("20", product_id=1)])

    (item,) = service.search(ProductFilters()).items

    assert item.price.list_price == Decimal("250.00")
    assert item.price.final_price == Decimal("200.00")


# Categories listing


def test_list_categories_counts_only_available_products_and_collects_their_colors():
    service = search_service(
        [
            make_product(1, category_id=1, specs={"color": "Red"}),
            make_product(2, category_id=1, specs={"color": "Black"}),
            make_product(3, category_id=1, specs={"color": "Black"}),
            make_product(4, category_id=1, stock=0, specs={"color": "Blue"}),
            make_product(5, category_id=1, status="discontinued", specs={"color": "Green"}),
        ]
    )

    guitars = {summary.id: summary for summary in service.list_categories()}[1]

    assert guitars.available_products == 3
    assert guitars.colors == ["Black", "Red"]


def test_list_categories_includes_empty_categories():
    service = search_service([make_product(1, category_id=1)])

    summaries = {summary.id: summary for summary in service.list_categories()}

    assert set(summaries) == {1, 2, 3}
    assert summaries[3].available_products == 0
    assert summaries[3].colors == []


# Real store data (these tests intentionally pin the delivered CSV files)


def test_store_search_by_instrument_finds_its_products(store_search: ProductSearchService):
    items = store_search.search(ProductFilters(query="ukulele")).items

    assert items
    assert {item.product.category_id for item in items} == {9}


def test_store_never_offers_unavailable_products_by_default(store_search: ProductSearchService):
    result = store_search.search(ProductFilters())

    assert result.items
    assert {item.product.availability for item in result.items} == {Availability.AVAILABLE}


def test_store_black_includes_the_products_registered_as_preto(store_search: ProductSearchService):
    names = [item.product.name for item in store_search.search(ProductFilters(color="black")).items]

    assert any("Shelby SN-100" in name for name in names)
