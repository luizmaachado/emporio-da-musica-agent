"""The agent and the CLI reply, with a fake model: no LLM and no network."""
from collections.abc import Sequence
from typing import Any, override

from langchain_core.language_models.fake_chat_models import GenericFakeChatModel
from langchain_core.messages import AIMessage, BaseMessage, SystemMessage
from langchain_core.runnables import Runnable, RunnableConfig

from emporio.agent.agent import build_agent
from emporio.agent.prompt import SYSTEM_PROMPT
from emporio.cli import reply
from emporio.data.policies import load_policy_sections
from tests.agent.fakes import WordEmbeddings


class FakeChatModel(GenericFakeChatModel):
    """The fake model has no tool binding; the agent only needs `bind_tools` to exist."""

    @override
    def bind_tools(self, tools: Sequence[Any], *, tool_choice: str | None = None, **kwargs: Any) -> Runnable[Any, Any]:
        return self


EMBEDDINGS = WordEmbeddings()


def fake_model(*answers: str) -> FakeChatModel:
    return FakeChatModel(messages=iter([AIMessage(content=answer) for answer in answers]))


def config(thread: str) -> RunnableConfig:
    return RunnableConfig(configurable={"thread_id": thread})


def test_the_agent_answers_a_message():
    agent = build_agent(fake_model("Olá! Como posso ajudar?"), EMBEDDINGS)

    turn = reply(agent, config("a"), "oi")

    assert turn.answer == "Olá! Como posso ajudar?"
    assert turn.tool_calls == ()
    assert turn.seconds >= 0


def test_the_history_is_kept_per_thread():
    agent = build_agent(fake_model("primeira", "segunda"), EMBEDDINGS)
    _ = reply(agent, config("a"), "um")
    _ = reply(agent, config("a"), "dois")

    messages = agent.get_state(config("a")).values["messages"]

    assert [m.content for m in messages] == ["um", "primeira", "dois", "segunda"]


RECORDED_CALLS: list[list[BaseMessage]] = []


class RecordingModel(FakeChatModel):
    """Keeps the messages of every call, so a test can see the prompt the model received."""

    @override
    def _generate(self, messages: list[BaseMessage], *args: Any, **kwargs: Any) -> Any:
        RECORDED_CALLS.append(list(messages))
        return super()._generate(messages, *args, **kwargs)


def recorded_system_prompt(question: str, **options: Any) -> str:
    model = RecordingModel(messages=iter([AIMessage(content="ok")]))
    RECORDED_CALLS.clear()
    agent = build_agent(model, EMBEDDINGS, **options)
    _ = reply(agent, config("a"), question)
    system = RECORDED_CALLS[0][0]
    assert isinstance(system, SystemMessage)
    return str(system.content)


def test_the_manual_sections_reach_the_model_in_the_system_prompt():
    only_hours = [s for s in load_policy_sections() if s.number == "2"]

    prompt = recorded_system_prompt("vocês abrem no sábado?", sections=only_hours)

    assert prompt.startswith(SYSTEM_PROMPT)
    assert "REGRAS DA LOJA PARA ESTA PERGUNTA" in prompt
    assert "Sábado 09:00 às 13:00" in prompt
    assert "Regras de Parcelamento" not in prompt  # only the sections that were passed in


def test_the_prompt_stays_plain_when_no_section_passes_the_cutoff():
    prompt = recorded_system_prompt("trombone afinado", policy_min_score=0.99)

    assert prompt == SYSTEM_PROMPT
