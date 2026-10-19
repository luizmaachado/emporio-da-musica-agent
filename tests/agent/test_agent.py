"""The agent and the CLI reply, with a fake model: no LLM and no network."""
from collections.abc import Sequence
from typing import Any, override

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage
from langchain_core.runnables import Runnable, RunnableConfig

from emporio.agent.agent import build_agent
from emporio.cli import reply


class FakeChatModel(GenericFakeChatModel):
    """The fake model has no tool binding; the agent only needs `bind_tools` to exist."""

    @override
    def bind_tools(self, tools: Sequence[Any], *, tool_choice: str | None = None, **kwargs: Any) -> Runnable[Any, Any]:
        return self


def fake_model(*answers: str) -> FakeChatModel:
    return FakeChatModel(messages=iter([AIMessage(content=answer) for answer in answers]))


def config(thread: str) -> RunnableConfig:
    return RunnableConfig(configurable={"thread_id": thread})


def test_the_agent_answers_a_message():
    agent = build_agent(fake_model("Olá! Como posso ajudar?"))

    turn = reply(agent, config("a"), "oi")

    assert turn.answer == "Olá! Como posso ajudar?"
    assert turn.tool_calls == ()
    assert turn.seconds >= 0


def test_the_history_is_kept_per_thread():
    agent = build_agent(fake_model("primeira", "segunda"))
    _ = reply(agent, config("a"), "um")
    _ = reply(agent, config("a"), "dois")

    messages = agent.get_state(config("a")).values["messages"]

    assert [m.content for m in messages] == ["um", "primeira", "dois", "segunda"]
