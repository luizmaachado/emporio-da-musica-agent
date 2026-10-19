"""Agent tools: arguments in, compact data out, domain errors as data."""
from decimal import Decimal
from typing import Any

import pytest
from langchain_core.tools import BaseTool

from emporio.agent.tools import build_tools, format_brl, format_percent
from emporio.services.search import ProductSearchService
from tests.factories import make_category, make_product, make_promotion


@pytest.fixture
def tools() -> dict[str, BaseTool]:
    products = [
        make_product(
            1, "1000.00", name="Yamaha C40", category_id=1,
            specs={"color": "Natural", "strings": "nylon", "electronics": "yes"},
        ),
        make_product(2, "500.00", name="Old model", category_id=1, status="discontinued"),
        make_product(3, "300.00", name="Sold out", category_id=1, stock=0),
        make_product(4, "200.00", name="Cheap", category_id=1, specs={"color": "Black"}),
    ]
    search = ProductSearchService(
        products,
        [make_category(1, "Violões"), make_category(2, "Sopros")],
        [make_promotion("10", 1)],
    )
    return {tool.name: tool for tool in build_tools(search)}


def names(result: dict[str, Any]) -> list[str]:
    return [item["name"] for item in result["items"]]


def test_the_agent_gets_both_catalog_tools(tools: dict[str, BaseTool]):
    # The prompt refers to these names.
    assert set(tools) == {"search_products", "list_categories"}


def test_search_products_returns_prices_and_promotion(tools: dict[str, BaseTool]):
    result = tools["search_products"].invoke({"query": "yamaha"})

    (item,) = result["items"]
    assert result["total"] == 1
    assert item["list_price"] == "R$ 1.000,00"
    assert item["final_price"] == "R$ 900,00"
    assert item["discount_percent"] == "10%"
    assert item["availability"] == "available"


def test_a_product_without_promotion_has_no_discount(tools: dict[str, BaseTool]):
    result = tools["search_products"].invoke({"query": "cheap"})

    (item,) = result["items"]
    assert item["discount_percent"] is None
    assert item["promotion_name"] is None
    assert item["final_price"] == item["list_price"] == "R$ 200,00"


def test_unavailable_products_are_labelled_when_requested(tools: dict[str, BaseTool]):
    result = tools["search_products"].invoke({"include_unavailable": True})

    availability = {item["name"]: item["availability"] for item in result["items"]}
    assert availability == {
        "Cheap": "available",
        "Sold out": "out_of_stock",
        "Old model": "unavailable",
        "Yamaha C40": "available",
    }


def test_filters_reach_the_search(tools: dict[str, BaseTool]):
    search = tools["search_products"]

    assert names(search.invoke({"color": "black"})) == ["Cheap"]
    assert names(search.invoke({"string_type": "nylon"})) == ["Yamaha C40"]
    assert names(search.invoke({"electronics": True})) == ["Yamaha C40"]
    assert names(search.invoke({"sort": "price_desc"})) == ["Yamaha C40", "Cheap"]


def test_search_products_reports_a_domain_error_instead_of_raising(tools: dict[str, BaseTool]):
    result = tools["search_products"].invoke({"category_id": 99})

    assert result["error"] == "UNKNOWN_CATEGORY"


def test_search_products_reports_an_invalid_price_range(tools: dict[str, BaseTool]):
    result = tools["search_products"].invoke({"min_price": 10, "max_price": 5})

    assert result["error"] == "INVALID_PRICE_RANGE"


def test_search_without_results_reports_the_criteria_that_were_applied(
    tools: dict[str, BaseTool],
):
    result = tools["search_products"].invoke({"category_id": 1, "max_price": 100})

    assert result["total"] == 0
    assert result["items"] == []
    assert result["filters"] == {"category_id": 1, "max_price": "100.00"}


def test_the_results_carry_facts_only_no_instructions(tools: dict[str, BaseTool]):
    result = tools["search_products"].invoke({"query": "yamaha"})

    assert set(result) == {"total", "filters", "items"}


def test_a_zero_price_bound_is_ignored(tools: dict[str, BaseTool]):
    with_zeros = tools["search_products"].invoke({"min_price": 0, "max_price": 0})
    without = tools["search_products"].invoke({})

    assert names(with_zeros) == names(without) != []


def test_list_categories_returns_counts_and_colors(tools: dict[str, BaseTool]):
    categories = tools["list_categories"].invoke({})

    assert [(c["id"], c["available_products"], c["colors"]) for c in categories] == [
        (1, 2, ["Black", "Natural"]),
        (2, 0, []),
    ]


@pytest.mark.parametrize(
    ("amount", "expected"),
    [("1299.9", "R$ 1.299,90"), ("49", "R$ 49,00"), ("0", "R$ 0,00"), ("0.5", "R$ 0,50")],
)
def test_money_is_formatted_in_brazilian_style(amount: str, expected: str):
    assert format_brl(Decimal(amount)) == expected


@pytest.mark.parametrize(
    ("percent", "expected"), [("10", "10%"), ("12.5", "12,5%"), ("100", "100%"), ("5.00", "5%")]
)
def test_percent_is_formatted_without_scientific_notation(percent: str, expected: str):
    assert format_percent(Decimal(percent)) == expected
