"""Policy retrieval: which manual sections reach the prompt, and when none do."""
import pytest
from langchain_core.messages import AIMessage, AnyMessage, HumanMessage

from emporio.agent.policies import (
    PolicyRetriever,
    policy_context,
    prompt_with_policies,
    retrieval_query,
)
from emporio.data.policies import load_policy_sections
from emporio.domain.policies import PolicySection
from tests.agent.fakes import WordEmbeddings


def section(number: str, title: str, text: str) -> PolicySection:
    return PolicySection(number=number, title=title, text=text)


SECTIONS = [
    section("1", "Pagamento", "Pagamento por PIX com desconto e cartão de crédito parcelado"),
    section("2", "Horário", "Horário de funcionamento de segunda a sexta das nove às dezoito"),
    section("3", "Frete", "Frete grátis e entrega por motoboy na região metropolitana"),
]


def retriever(**options: float | None) -> PolicyRetriever:
    return PolicyRetriever(SECTIONS, WordEmbeddings(), **options)  # pyright: ignore[reportArgumentType]


def test_the_closest_section_comes_first():
    hits = retriever(min_score=0.1).retrieve("qual o horário de funcionamento")

    assert hits[0].section.number == "2"


def test_there_is_no_cutoff_by_default():
    hits = retriever().retrieve("trombone afinado")

    assert len(hits) == 3


def test_nothing_is_retrieved_when_even_the_best_section_is_below_the_threshold():
    assert retriever(min_score=0.5).retrieve("trombone afinado") == []


def test_once_the_best_section_passes_the_next_ones_come_along():
    hits = retriever(top_k=3, min_score=0.3).retrieve("horário de funcionamento")

    assert hits[0].section.number == "2"
    assert len(hits) == 3
    assert hits[0].score >= 0.3 > hits[-1].score


def test_at_most_top_k_sections_are_returned():
    hits = retriever(top_k=2, min_score=0.0).retrieve("pagamento horário frete")

    assert len(hits) == 2


def test_a_blank_question_retrieves_nothing():
    assert retriever(min_score=0.0).retrieve("   ") == []


def test_the_context_names_each_section_and_is_empty_without_hits():
    hits = retriever(min_score=0.1).retrieve("horário de funcionamento")

    context = policy_context(hits)

    assert "[2 Horário]" in context
    assert "segunda a sexta" in context
    assert policy_context([]) == ""


def test_the_query_uses_the_last_two_customer_messages():
    messages: list[AnyMessage] = [
        HumanMessage("vocês abrem sábado?"),
        AIMessage("Abrimos das 9h às 13h."),
        HumanMessage("e domingo?"),
    ]
    messages.insert(0, HumanMessage("oi"))

    assert retrieval_query(messages) == "vocês abrem sábado?\ne domingo?"


def test_the_prompt_is_unchanged_when_nothing_matches():
    prompt = prompt_with_policies("BASE", retriever(min_score=0.5), [HumanMessage("trombone")])

    assert prompt == "BASE"


def test_the_prompt_gets_the_matching_sections():
    prompt = prompt_with_policies(
        "BASE", retriever(min_score=0.1), [HumanMessage("qual o horário de funcionamento")]
    )

    assert prompt.startswith("BASE")
    assert "REGRAS DA LOJA PARA ESTA PERGUNTA" in prompt
    assert "Horário" in prompt


def test_the_context_tells_the_model_not_to_mention_the_manual_or_sections():
    context = policy_context(retriever(min_score=0.1).retrieve("horário de funcionamento"))

    assert "nunca mencione manual, seção" in context


def test_the_whole_real_manual_can_be_indexed_and_searched():
    manual = PolicyRetriever(load_policy_sections(), WordEmbeddings(), min_score=0.1)  # pyright: ignore[reportArgumentType]

    hits = manual.retrieve("Regras de Parcelamento")

    assert "3.1" in {hit.section.number for hit in hits}


def test_top_k_must_be_at_least_one():
    with pytest.raises(ValueError, match="top_k"):
        _ = retriever(top_k=0)
