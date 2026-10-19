"""Checks that an answer only states what the tools returned in the conversation.

It is a cheap, deterministic safety net for manual testing, not a proof of correctness:

- every price in the answer must appear in a tool result (or be a price bound the model sent to
  a tool, such as the budget the customer gave);
- every **bold** fragment must appear in a tool result, which catches invented product names.

Known limits: opinions are not checked, nor are colors, stock, percentages or products written
without bold. A price bound the model invented counts as evidence. Bold text is matched as a
substring, so a short fragment ("Yamaha") passes if it appears anywhere in the results. Prices
are read in the Brazilian format ("1.299,90"); "1299.90" would raise a false alert.
"""
import re
from collections.abc import Sequence
from decimal import Decimal, InvalidOperation

from langchain_core.messages import AIMessage, AnyMessage, ToolMessage

from emporio.agent.messages import content_text
from emporio.agent.tools import format_brl
from emporio.domain.text import normalize_text

_PRICE = re.compile(r"R\$\s?(\d[\d.]*(?:,\d{1,2})?)")
_BOLD = re.compile(r"\*\*(.+?)\*\*")
_PRICE_ARGUMENTS = ("min_price", "max_price")


def _amount(text: str) -> Decimal | None:
    try:
        return Decimal(text.replace(".", "").replace(",", "."))
    except InvalidOperation:
        return None


def _amounts(text: str) -> set[Decimal]:
    return {amount for match in _PRICE.findall(text) if (amount := _amount(match)) is not None}


def _evidence(messages: Sequence[AnyMessage]) -> tuple[str, set[Decimal]]:
    """All tool results of the conversation, and the price bounds the model sent to tools."""
    results = " ".join(content_text(m.content) for m in messages if isinstance(m, ToolMessage))
    bounds = {
        Decimal(str(value))
        for m in messages
        if isinstance(m, AIMessage)
        for call in m.tool_calls
        for name in _PRICE_ARGUMENTS
        if isinstance(value := call["args"].get(name), int | float)
    }
    return normalize_text(results), _amounts(results) | bounds


def check_grounding(answer: str, messages: Sequence[AnyMessage]) -> list[str]:
    """Problems found in `answer`, given the conversation `messages`; empty means none found."""
    evidence_text, evidence_amounts = _evidence(messages)
    problems = [
        f"price {format_brl(amount)} was not returned by any tool"
        for amount in sorted(_amounts(answer) - evidence_amounts)
    ]
    for fragment in dict.fromkeys(_BOLD.findall(answer)):
        if fragment.startswith("R$"):
            continue
        if normalize_text(fragment) not in evidence_text:
            problems.append(f"'{fragment}' was not returned by any tool")
    return problems

