"""The grounding check: what the answer says must come from the tools of the conversation."""
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, ToolMessage

from emporio.agent.grounding import check_grounding

RESULT = (
    '{"total": 1, "items": [{"name": "Tagima Memphis AC-39 Nylon Natural", "final_price": '
    '"R$ 1.299,90", "specs": {"scale": "650mm", "top": "Linden"}}]}'
)


def conversation(*, budget: float | None = None) -> list[AnyMessage]:
    args: dict[str, object] = {"query": "memphis"}
    if budget is not None:
        args["max_price"] = budget
    return [
        HumanMessage("memphis"),
        AIMessage(content="", tool_calls=[{"name": "search_products", "args": args, "id": "1"}]),
        ToolMessage(RESULT, tool_call_id="1"),
    ]


def test_an_answer_built_from_the_results_has_no_problems():
    answer = "O **Tagima Memphis AC-39 Nylon Natural** custa **R$ 1.299,90**, escala **650mm**."

    assert check_grounding(answer, conversation()) == []


def test_an_invented_product_is_reported():
    answer = "Temos o **Fender Precision Bass** por R$ 1.299,90."

    assert check_grounding(answer, conversation()) == [
        "'Fender Precision Bass' was not returned by any tool"
    ]


def test_an_invented_price_is_reported():
    answer = "O **Tagima Memphis AC-39 Nylon Natural** custa R$ 999,00."

    assert check_grounding(answer, conversation()) == [
        "price R$ 999,00 was not returned by any tool"
    ]


def test_a_price_bound_sent_to_a_tool_may_be_repeated():
    answer = "Violões até R$ 1.500: o **Tagima Memphis AC-39 Nylon Natural**."

    assert check_grounding(answer, conversation(budget=1500)) == []


def test_matching_ignores_case_and_accents():
    answer = "Tampo de **LINDEN**."

    assert check_grounding(answer, conversation()) == []


def test_a_price_with_no_tool_call_at_all_is_reported():
    answer = "Custa R$ 500,00."

    assert check_grounding(answer, [HumanMessage("preço?")]) == [
        "price R$ 500,00 was not returned by any tool"
    ]


def test_results_of_earlier_turns_count_as_evidence():
    messages = [*conversation(), AIMessage("ok"), HumanMessage("e a escala?")]

    assert check_grounding("A escala é **650mm**.", messages) == []


def test_a_bold_price_is_checked_as_a_price_not_as_a_name():
    assert check_grounding("Custa **R$ 1.299,90**.", conversation()) == []


def test_a_price_at_the_end_of_a_sentence_and_one_without_cents_are_read():
    assert check_grounding("Fica R$ 1.299,90.", conversation()) == []
    assert check_grounding("Fica em R$ 1.500.", conversation(budget=1500)) == []


def test_every_problem_is_reported_in_order():
    answer = "O **Fender X** custa R$ 5,00 e o **Gibson Y** R$ 6,00."

    assert check_grounding(answer, conversation()) == [
        "price R$ 5,00 was not returned by any tool",
        "price R$ 6,00 was not returned by any tool",
        "'Fender X' was not returned by any tool",
        "'Gibson Y' was not returned by any tool",
    ]


def test_tool_results_in_content_blocks_count_as_evidence():
    messages = [
        HumanMessage("memphis"),
        ToolMessage([{"type": "text", "text": "Tagima Memphis AC-39"}], tool_call_id="1"),
    ]

    assert check_grounding("Temos o **Tagima Memphis AC-39**.", messages) == []
