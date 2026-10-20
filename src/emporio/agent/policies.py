"""Policy retrieval: the manual sections closest in meaning to what the customer wrote.

The retrieval is automatic (no tool): on every turn the closest sections are added to the
system prompt. A small model does not reliably decide to look a policy up, and the manual is
small enough (about 20 sections) for a few extra sections per turn to cost little.

There is no similarity cutoff by default. One was tried (0.48 with bge-m3) and failed on
questions it should have answered ("what is your CNPJ?", "since when does the store exist?")
while product questions that leaked through did no harm, so `min_score` is only an option.
"""
from collections.abc import Sequence
from dataclasses import dataclass

from langchain_core.documents import Document
from langchain_core.embeddings import Embeddings
from langchain_core.messages import AnyMessage
from langchain_core.vectorstores import InMemoryVectorStore

from emporio.agent.messages import content_text
from emporio.domain.policies import PolicySection

DEFAULT_TOP_K = 3
DEFAULT_MIN_SCORE: float | None = None  # cosine similarity of the best section


@dataclass(frozen=True)
class PolicyHit:
    section: PolicySection
    score: float


class PolicyRetriever:
    """Semantic search over the manual sections, kept in memory."""

    def __init__(
        self,
        sections: Sequence[PolicySection],
        embeddings: Embeddings,
        *,
        top_k: int = DEFAULT_TOP_K,
        min_score: float | None = DEFAULT_MIN_SCORE,
    ) -> None:
        """Embeds every section once, here.

        Raises:
            ValueError: when `top_k` is below 1.
        """
        if top_k < 1:
            raise ValueError("top_k must be at least 1.")
        self._by_number = {section.number: section for section in sections}
        self._top_k = top_k
        self._min_score = min_score
        self._store = InMemoryVectorStore(embeddings)
        _ = self._store.add_documents(
            [
                Document(
                    page_content=f"{section.heading}\n{section.text}",
                    metadata={"number": section.number},
                )
                for section in sections
            ]
        )

    def retrieve(self, query: str) -> list[PolicyHit]:
        """The `top_k` closest sections, best first. With a `min_score`, none if even the best
        scores below it."""
        if not query.strip():
            return []
        results = self._store.similarity_search_with_score(query, k=self._top_k)
        if not results or (self._min_score is not None and results[0][1] < self._min_score):
            return []
        return [
            PolicyHit(self._by_number[document.metadata["number"]], score)
            for document, score in results
        ]


_POLICY_INSTRUCTIONS = (
    "\n\nREGRAS DA LOJA PARA ESTA PERGUNTA\n"
    "Use estes trechos apenas se forem relevantes para a pergunta do cliente. Responda com "
    "base neles, sem inventar prazos, valores ou condições. Fale como a própria loja "
    "(\"nosso prazo é...\"): o cliente não conhece o manual interno, então nunca mencione "
    "manual, seção ou número de seção. Se a resposta não estiver aqui, diga que não tem "
    "essa informação.\n\n"
)


def policy_context(hits: Sequence[PolicyHit]) -> str:
    """The block appended to the system prompt; empty when nothing was retrieved."""
    if not hits:
        return ""
    sections = "\n\n".join(f"[{hit.section.heading}]\n{hit.section.text}" for hit in hits)
    return f"{_POLICY_INSTRUCTIONS}{sections}"


def retrieval_query(messages: Sequence[AnyMessage]) -> str:
    """What to search for: the last two customer messages, so a follow-up ("e no sábado?")
    keeps the subject of the previous question."""
    customer = [content_text(m.content) for m in messages if m.type == "human"]
    return "\n".join(customer[-2:])


def prompt_with_policies(
    base_prompt: str, retriever: PolicyRetriever, messages: Sequence[AnyMessage]
) -> str:
    """The system prompt for this turn: the base prompt plus the sections that match."""
    return base_prompt + policy_context(retriever.retrieve(retrieval_query(messages)))
