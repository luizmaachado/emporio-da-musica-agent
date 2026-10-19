"""Checks that an answer only states what the tools returned in the conversation.

It is a cheap, deterministic safety net for manual testing, not a proof of correctness:

- every price in the answer must appear in a tool result or in the manual, or be an amount the
  customer wrote, or a price bound the model sent to a tool (such as the budget);
- every **bold** fragment must appear in a tool result or in the manual, which catches invented
  product names.

Known limits: the evidence is the whole customer-facing manual, not only the sections retrieved
for the turn; a price the model computed itself (an installment, a total) is reported, since no
source has it; opinions are not checked, nor are colors, stock, percentages or products written
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
_NUMBER = r"\d[\d.]*(?:,\d{1,2})?"
_CUSTOMER_AMOUNT = re.compile(rf"R\$\s?({_NUMBER})|({_NUMBER})\s*reais?")


def _amount(text: str) -> Decimal | None:
    try:
        return Decimal(text.replace(".", "").replace(",", "."))
    except InvalidOperation:
        return None


def _amounts(text: str) -> set[Decimal]:
    return {amount for match in _PRICE.findall(text) if (amount := _amount(match)) is not None}


def _evidence(messages: Sequence[AnyMessage], manual: str) -> tuple[str, set[Decimal]]:
    """All tool results of the conversation and the manual, and the price bounds the model sent
    to tools."""
    results = " ".join(
        [*(content_text(m.content) for m in messages if isinstance(m, ToolMessage)), manual]
    )
    bounds = {
        Decimal(str(value))
        for m in messages
        if isinstance(m, AIMessage)
        for call in m.tool_calls
        for name in _PRICE_ARGUMENTS
        if isinstance(value := call["args"].get(name), int | float)
    }
    # Amounts the customer wrote with R$ or "reais" may be repeated back; "6x" is not an amount.
    customer = {
        amount
        for m in messages
        if m.type == "human"
        for groups in _CUSTOMER_AMOUNT.findall(content_text(m.content))
        if (amount := _amount(groups[0] or groups[1])) is not None
    }
    return normalize_text(results), _amounts(results) | bounds | customer


def check_grounding(answer: str, messages: Sequence[AnyMessage], manual: str = "") -> list[str]:
    """Problems found in `answer`, given the conversation `messages` and the text of the store
    manual; empty means none found."""
    evidence_text, evidence_amounts = _evidence(messages, manual)
    problems = [
        f"price {format_brl(amount)} was not found in the tool results or the manual"
        for amount in sorted(_amounts(answer) - evidence_amounts)
    ]
    for fragment in dict.fromkeys(_BOLD.findall(answer)):
        if fragment.startswith("R$"):
            continue
        if normalize_text(fragment) not in evidence_text:
            problems.append(f"'{fragment}' was not found in the tool results or the manual")
    return problems

