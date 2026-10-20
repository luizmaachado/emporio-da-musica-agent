"""Text helpers for matching what customers type against catalog text."""
import unicodedata


def normalize_text(text: str) -> str:
    """Lowercase and strip accents, so "Violão" and "violao" compare equal."""
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))
