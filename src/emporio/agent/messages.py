"""Helpers for reading LangChain messages."""
import json
from collections.abc import Mapping, Sequence


def content_text(content: str | Sequence[object]) -> str:
    """The text of a message. Providers may send a list of content blocks instead of a string.

    Plain strings and the `text` of text blocks are joined; any other block is kept as JSON so
    nothing the model saw is silently dropped.
    """
    if isinstance(content, str):
        return content
    parts: list[str] = []
    for block in content:
        if isinstance(block, str):
            parts.append(block)
        elif isinstance(block, Mapping) and "text" in block:
            parts.append(str(block["text"]))  # pyright: ignore[reportUnknownArgumentType]
        else:
            parts.append(json.dumps(block, ensure_ascii=False, default=str))
    return "".join(parts)
