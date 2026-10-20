"""CLI helpers: the turn, its trace and the failure of the model."""
from typing import Any

import pytest
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage, ToolMessage
from langchain_core.runnables import RunnableConfig

from emporio import cli
from emporio.agent.agent import Agent
from emporio.cli import (
    ModelUnavailable,
    StartupError,
    format_trace,
    reply,
    start_agent,
    turn_from,
)


def search_conversation(answer: str | list[str | dict[str, Any]]) -> list[AnyMessage]:
    messages: list[AnyMessage] = [
        HumanMessage("violão?"),
        AIMessage(
            content="",
            tool_calls=[{"name": "search_products", "args": {"category_id": 5}, "id": "1"}],
        ),
        ToolMessage('{"total": 1, "items": [{"name": "Yamaha C40"}]}', tool_call_id="1"),
        AIMessage(content=answer),
    ]
    return messages


def test_the_trace_shows_time_each_call_and_the_grounding_result():
    turn = turn_from(search_conversation("Temos o **Yamaha C40**."), 12.34)

    assert format_trace(turn) == (
        "[trace] 12.3s, 1 tool call(s)\n"
        "[trace]   search_products(category_id=5) -> 1 products\n"
        "[trace]   grounding: no ungrounded prices or names found"
    )


def test_the_trace_shows_each_alert():
    turn = turn_from(search_conversation("Temos o **Fender X** por R$ 9,00."), 1.0)

    trace = format_trace(turn)

    assert "ALERT: price R$ 9,00 was not found in the tool results or the manual" in trace
    assert "ALERT: 'Fender X' was not found in the tool results or the manual" in trace


def test_an_answer_in_content_blocks_is_read_as_plain_text():
    turn = turn_from(search_conversation([{"type": "text", "text": "Temos o **Yamaha C40**."}]), 1.0)

    assert turn.answer == "Temos o **Yamaha C40**."
    assert turn.problems == ()


class BrokenAgent:
    def invoke(self, *_args: Any, **_kwargs: Any) -> dict[str, Any]:
        raise ConnectionError("ollama is down")


def test_a_model_failure_becomes_model_unavailable():
    agent: Agent = BrokenAgent()  # pyright: ignore[reportAssignmentType]

    with pytest.raises(ModelUnavailable, match="ConnectionError"):
        _ = reply(agent, RunnableConfig(), "oi")


def test_a_price_from_the_manual_is_grounded_only_when_the_manual_is_passed():
    messages = search_conversation("A parcela mínima é R$ 80,00.")

    assert turn_from(messages, 1.0).problems != ()
    assert turn_from(messages, 1.0, "Parcela mínima de R$ 80,00").problems == ()


def test_startup_explains_what_to_check_when_ollama_is_unavailable(
    monkeypatch: pytest.MonkeyPatch,
):
    def unavailable() -> object:
        raise ConnectionError("ollama is down")

    monkeypatch.setattr(cli, "build_embeddings", unavailable)

    with pytest.raises(StartupError, match="Ollama"):
        _ = start_agent()


def test_startup_reports_an_invalid_configuration(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LLM_PROVIDER", "nope")

    with pytest.raises(StartupError, match="Configuração inválida"):
        _ = start_agent()
