"""Reading the tool calls of the last turn out of the message history."""
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, ToolMessage

from emporio.agent.trace import ToolCall, tool_calls_of_last_turn


def call_message(name: str, args: dict[str, object], call_id: str) -> AIMessage:
    return AIMessage(content="", tool_calls=[{"name": name, "args": args, "id": call_id}])


def test_only_the_calls_after_the_last_customer_message_are_reported():
    messages: list[AnyMessage] = [
        HumanMessage("primeira"),
        call_message("list_categories", {}, "1"),
        ToolMessage('[{"id": 5}]', tool_call_id="1"),
        AIMessage("resposta"),
        HumanMessage("segunda"),
        call_message("search_products", {"category_id": 5}, "2"),
        ToolMessage('{"total": 15, "items": []}', tool_call_id="2"),
        AIMessage("resposta 2"),
    ]

    (call,) = tool_calls_of_last_turn(messages)

    assert call.name == "search_products"
    assert call.args == {"category_id": 5}
    assert call.outcome() == "15 products"


def test_a_domain_error_is_summarized_by_its_code():
    messages: list[AnyMessage] = [
        HumanMessage("oi"),
        call_message("search_products", {"category_id": 99}, "1"),
        ToolMessage('{"error": "UNKNOWN_CATEGORY", "message": "x"}', tool_call_id="1"),
    ]

    (call,) = tool_calls_of_last_turn(messages)

    assert call.summary() == "search_products(category_id=99) -> error UNKNOWN_CATEGORY"


def test_a_turn_without_tools_has_no_calls():
    assert tool_calls_of_last_turn([HumanMessage("oi"), AIMessage("olá")]) == []


def outcome(result: str) -> str:
    return ToolCall("tool", {}, result).outcome()


def test_outcome_summarizes_the_usual_json_results():
    assert outcome('{"total": 3, "items": []}') == "3 products"
    assert outcome('{"error": "UNKNOWN_CATEGORY"}') == "error UNKNOWN_CATEGORY"
    assert outcome("[1, 2]") == "2 items"


def test_outcome_falls_back_to_the_start_of_the_raw_text():
    assert outcome("Error invoking tool " + "x" * 200) == ("Error invoking tool " + "x" * 200)[:80]
    assert outcome('{"other": 1}') == '{"other": 1}'
    assert outcome("42") == "42"
