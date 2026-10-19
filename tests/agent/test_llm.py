"""Model selection from environment variables."""
import pytest
from langchain_ollama import ChatOllama

from emporio.agent.llm import LLMConfigError, build_chat_model

_VARIABLES = (
    "LLM_PROVIDER", "LLM_MODEL", "OLLAMA_BASE_URL", "LLM_REASONING", "OLLAMA_NUM_CTX",
)


@pytest.fixture(autouse=True)
def clean_environment(monkeypatch: pytest.MonkeyPatch):
    for name in _VARIABLES:
        monkeypatch.delenv(name, raising=False)


def test_ollama_with_the_default_model_is_used_when_nothing_is_set():
    model = build_chat_model()

    assert isinstance(model, ChatOllama)
    assert model.model == "qwen3:8b"
    assert model.reasoning is True
    assert model.num_ctx == 8192


def test_the_model_name_can_be_overridden(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LLM_MODEL", "qwen3:14b")

    model = build_chat_model()

    assert isinstance(model, ChatOllama)
    assert model.model == "qwen3:14b"


def test_reasoning_and_context_can_be_changed(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LLM_REASONING", "no")
    monkeypatch.setenv("OLLAMA_NUM_CTX", "4096")

    model = build_chat_model()

    assert isinstance(model, ChatOllama)
    assert model.reasoning is False
    assert model.num_ctx == 4096


def test_an_unsupported_provider_is_refused(monkeypatch: pytest.MonkeyPatch):
    monkeypatch.setenv("LLM_PROVIDER", "nope")

    with pytest.raises(LLMConfigError, match="LLM_PROVIDER"):
        _ = build_chat_model()


@pytest.mark.parametrize(("name", "value"), [("OLLAMA_NUM_CTX", "big"), ("LLM_REASONING", "maybe")])
def test_an_invalid_value_names_the_variable(
    monkeypatch: pytest.MonkeyPatch, name: str, value: str
):
    monkeypatch.setenv(name, value)

    with pytest.raises(LLMConfigError, match=name):
        _ = build_chat_model()
