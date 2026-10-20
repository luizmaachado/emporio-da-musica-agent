"""What happened during one agent turn: which tools were called, with what, and what came back."""
import json
from collections.abc import Sequence
from dataclasses import dataclass

from langchain_core.messages import AIMessage, AnyMessage, BaseMessage, ToolMessage

from emporio.agent.messages import content_text

_MAX_OUTCOME_CHARS = 80


@dataclass(frozen=True)
class ToolCall:
    name: str
    args: dict[str, object]
    result: str  # the raw text the model received

    def summary(self) -> str:
        """One line for a human: the call, and the gist of what came back."""
        arguments = ", ".join(f"{key}={value!r}" for key, value in self.args.items())
        return f"{self.name}({arguments}) -> {self.outcome()}"

    def outcome(self) -> str:
        """What came back: a count or an error code when the result is the usual JSON."""
        try:
            data = json.loads(self.result)
        except json.JSONDecodeError:
            return self.result[:_MAX_OUTCOME_CHARS]
        if isinstance(data, list):
            return f"{len(data)} items"  # pyright: ignore[reportUnknownArgumentType]
        if isinstance(data, dict):
            if "error" in data:
                return f"error {data['error']}"  # pyright: ignore[reportUnknownVariableType]
            if "total" in data:
                return f"{data['total']} products"  # pyright: ignore[reportUnknownVariableType]
        return self.result[:_MAX_OUTCOME_CHARS]


def tool_calls_of_last_turn(messages: Sequence[AnyMessage]) -> list[ToolCall]:
    """Tool calls made after the last customer message, paired with the results they got."""
    last_human = max((i for i, m in enumerate(messages) if m.type == "human"), default=-1)
    turn: Sequence[BaseMessage] = messages[last_human + 1 :]
    results = {m.tool_call_id: content_text(m.content) for m in turn if isinstance(m, ToolMessage)}
    return [
        ToolCall(call["name"], dict(call["args"]), results.get(call["id"] or "", ""))
        for message in turn
        if isinstance(message, AIMessage)
        for call in message.tool_calls
    ]

