"""Chat model selection, driven by environment variables."""
import os
from types import MappingProxyType

from langchain_core.language_models.chat_models import BaseChatModel

DEFAULT_PROVIDER = "ollama"
DEFAULT_MODELS = MappingProxyType({"ollama": "qwen3:8b"})
_TRUE_VALUES = frozenset({"1", "true", "yes", "on"})
_FALSE_VALUES = frozenset({"0", "false", "no", "off"})


class LLMConfigError(ValueError):
    """An environment variable that configures the model is missing or invalid."""


def _env_bool(name: str, default: bool) -> bool:
    value = os.environ.get(name)
    if value is None or not value.strip():
        return default
    lowered = value.strip().lower()
    if lowered in _TRUE_VALUES:
        return True
    if lowered in _FALSE_VALUES:
        return False
    raise LLMConfigError(f"{name} must be true or false, got {value!r}.")


def _env_int(name: str, default: int) -> int:
    value = os.environ.get(name)
    if value is None or not value.strip():
        return default
    try:
        return int(value)
    except ValueError:
        raise LLMConfigError(f"{name} must be an integer, got {value!r}.") from None


def build_chat_model() -> BaseChatModel:
    """The model named by `LLM_PROVIDER` and `LLM_MODEL` (Ollama by default).

    Ollama also reads `OLLAMA_BASE_URL`, `LLM_REASONING` (on by default: the 8B model only
    calls tools reliably when it reasons first) and `OLLAMA_NUM_CTX`.

    Raises:
        LLMConfigError: when the provider is not supported or a variable is invalid.
    """
    provider = os.environ.get("LLM_PROVIDER", DEFAULT_PROVIDER).strip().lower()
    model = os.environ.get("LLM_MODEL") or DEFAULT_MODELS.get(provider, "")
    if provider == "ollama":
        # Imported here so that a provider's package is only needed when it is selected.
        from langchain_ollama import ChatOllama

        return ChatOllama(
            model=model,
            base_url=os.environ.get("OLLAMA_BASE_URL", "http://localhost:11434"),
            temperature=0,
            reasoning=_env_bool("LLM_REASONING", default=True),
            num_ctx=_env_int("OLLAMA_NUM_CTX", default=8192),
        )
    raise LLMConfigError(f"Unsupported LLM_PROVIDER: {provider!r}.")
