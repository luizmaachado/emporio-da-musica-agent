"""Command line chat with the agent: `uv run emporio`."""
import argparse
import time
import uuid
from collections.abc import Sequence
from dataclasses import dataclass

from dotenv import load_dotenv
from langchain_core.messages import AnyMessage
from langchain_core.runnables import RunnableConfig

from emporio.agent.agent import Agent, build_agent
from emporio.agent.grounding import check_grounding
from emporio.agent.llm import LLMConfigError, build_chat_model, build_embeddings
from emporio.agent.messages import content_text
from emporio.agent.trace import ToolCall, tool_calls_of_last_turn
from emporio.data.policies import load_policy_sections

EXIT_WORDS = frozenset({"sair", "exit", "quit"})


@dataclass(frozen=True)
class Turn:
    """One exchange: the answer, how long it took, the tools it used and what looks ungrounded."""

    answer: str
    seconds: float
    tool_calls: tuple[ToolCall, ...]
    problems: tuple[str, ...]


class ModelUnavailable(Exception):
    """The model could not answer (Ollama stopped, model missing, network error...)."""


def reply(agent: Agent, config: RunnableConfig, text: str, manual: str = "") -> Turn:
    """Send one customer message and return the agent's answer with its trace.

    `manual` is the text of the store manual, accepted as evidence by the grounding check.

    Raises:
        ModelUnavailable: when the call to the model fails. Errors in building the trace are
            not caught: they are bugs and should show their traceback.
    """
    started = time.monotonic()
    try:
        result = agent.invoke({"messages": [{"role": "user", "content": text}]}, config)
    except Exception as error:
        raise ModelUnavailable(type(error).__name__) from error
    return turn_from(result["messages"], time.monotonic() - started, manual)


def turn_from(messages: Sequence[AnyMessage], seconds: float, manual: str = "") -> Turn:
    """Build the turn from the conversation so far; the last message is the answer."""
    answer = content_text(messages[-1].content)
    return Turn(
        answer,
        seconds,
        tuple(tool_calls_of_last_turn(messages)),
        tuple(check_grounding(answer, messages, manual)),
    )


def format_trace(turn: Turn) -> str:
    """The trace block printed under an answer when `--trace` is on."""
    lines = [f"[trace] {turn.seconds:.1f}s, {len(turn.tool_calls)} tool call(s)"]
    lines += [f"[trace]   {call.summary()}" for call in turn.tool_calls]
    if turn.problems:
        lines += [f"[trace]   ALERT: {problem}" for problem in turn.problems]
    else:
        lines.append("[trace]   grounding: no ungrounded prices or names found")
    return "\n".join(lines)


class StartupError(Exception):
    """The agent could not start; the message tells the user what to check."""


def start_agent() -> tuple[Agent, str]:
    """The agent and the text of the manual it knows (used by the grounding check).

    Raises:
        StartupError: when the configuration is invalid or Ollama or its models are unavailable.
    """
    try:
        sections = load_policy_sections()
        agent = build_agent(build_chat_model(), build_embeddings(), sections)
    except LLMConfigError as error:
        raise StartupError(f"Configuração inválida: {error}") from error
    except Exception as error:
        raise StartupError(
            f"Não consegui iniciar o agente ({type(error).__name__}). O Ollama está rodando e "
            "os modelos foram baixados? Veja o README (ollama pull qwen3:8b e bge-m3)."
        ) from error
    return agent, "\n".join(section.text for section in sections)


def main() -> None:
    """Chat until the customer types an exit word. A new run starts a new conversation."""
    parser = argparse.ArgumentParser(description="Chat with the Empório da Música agent.")
    _ = parser.add_argument(
        "--trace", action="store_true", help="show time and tool calls under each answer"
    )
    trace = bool(parser.parse_args().trace)
    _ = load_dotenv()
    try:
        agent, manual = start_agent()
    except StartupError as error:
        print(error)
        raise SystemExit(1) from None
    config = RunnableConfig(configurable={"thread_id": str(uuid.uuid4())})
    print("Empório da Música — digite 'sair' para encerrar.\n")
    while True:
        try:
            text = input("Você: ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if text.lower() in EXIT_WORDS:
            break
        if not text:
            continue
        try:
            turn = reply(agent, config, text, manual)
        except ModelUnavailable as error:
            print(f"\nNão consegui falar com o modelo agora ({error}). Tente de novo.\n")
            continue
        print(f"\nAssistente: {turn.answer}\n")
        if trace:
            print(f"{format_trace(turn)}\n")


if __name__ == "__main__":
    main()
