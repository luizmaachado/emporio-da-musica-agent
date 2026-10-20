"""Reads the store manual (PDF) into numbered sections. The file is never modified."""
import re
from pathlib import Path

import pdfplumber

from emporio.domain.policies import PolicySection

POLICIES_PDF = Path(__file__).resolve().parents[3] / "data" / "políticas_da_loja.pdf"

# Sections that are of no use to a customer: the standard service flow (already in the agent
# prompt) and the manual's closing notes. The rest of section 7 stays: it holds facts customers
# ask about (WhatsApp response time, complaint deadline) and the rules for out-of-stock,
# discontinued and expired-promotion products.
INTERNAL_SECTIONS = frozenset({"7.2", "10"})

_HEADING = re.compile(r"^(\d+(?:\.\d+)*)\.?\s+(\S.*)$")
# Lines repeated on every page.
_PAGE_NOISE = re.compile(r"^(Página \d+|Empório da Música Manual de Políticas e Procedimentos)$")


def extract_pages(pdf_path: Path = POLICIES_PDF) -> list[str]:
    """The text of each page, one table row per line."""
    with pdfplumber.open(pdf_path) as pdf:
        return [page.extract_text() or "" for page in pdf.pages]


def _is_next_heading(number: str, previous: str | None) -> bool:
    """Whether `number` is the heading that follows `previous` in the manual's numbering.

    Numbered lists inside a section ("1. Saudação", "2. Entendimento") look like headings, so a
    number only counts when it is the next top-level section or the next subsection of the
    current one.
    """
    if previous is None:
        return number == "1"
    parts, previous_parts = number.split("."), previous.split(".")
    top, previous_top = int(parts[0]), int(previous_parts[0])
    if len(parts) == 1:
        return top == previous_top + 1
    if len(parts) != 2 or top != previous_top:
        return False
    last_minor = int(previous_parts[1]) if len(previous_parts) == 2 else 0
    return int(parts[1]) == last_minor + 1


def parse_sections(pages: list[str]) -> list[PolicySection]:
    """Splits the manual into sections, dropping page headers/footers and the cover.

    Sections with no text of their own (a title followed directly by subsections) are left out:
    their subsections carry the parent title instead.
    """
    lines = [
        line.strip()
        for page in pages
        for line in page.splitlines()
        if line.strip() and not _PAGE_NOISE.match(line.strip())
    ]
    headings: list[tuple[str, str]] = []
    bodies: list[list[str]] = []
    previous: str | None = None
    for line in lines:
        match = _HEADING.match(line)
        if match and _is_next_heading(match.group(1), previous):
            previous = match.group(1)
            headings.append((match.group(1), match.group(2)))
            bodies.append([])
        elif headings:  # text before the first heading is the cover
            bodies[-1].append(line)

    titles = {number: title for number, title in headings}
    sections: list[PolicySection] = []
    for (number, title), body in zip(headings, bodies, strict=True):
        if not body:
            continue
        parent = number.rsplit(".", 1)[0] if "." in number else None
        sections.append(
            PolicySection(
                number=number,
                title=title,
                parent_title=titles.get(parent) if parent else None,
                text="\n".join(body),
            )
        )
    return sections


def load_policy_sections(
    pdf_path: Path = POLICIES_PDF, *, include_internal: bool = False
) -> list[PolicySection]:
    """The manual's sections for customers; `include_internal` also returns the staff-only ones."""
    sections = parse_sections(extract_pages(pdf_path))
    if include_internal:
        return sections
    return [section for section in sections if section.number not in INTERNAL_SECTIONS]
