"""Retrieval quality with the real embeddings model (bge-m3 on Ollama).

Skipped when Ollama or the model is not available. If these fail after changing the model, the
manual or the chunking, the retrieval needs another look.
"""
import pytest
from langchain_core.embeddings import Embeddings

from emporio.agent.llm import build_embeddings
from emporio.agent.policies import PolicyRetriever
from emporio.data.policies import load_policy_sections

pytestmark = pytest.mark.integration

# (question, sections that answer it)
FIRST_QUESTIONS = [
    ("posso parcelar em 6x uma compra de 400 reais?", {"3.1", "3"}),
    ("vocês aceitam pix? tem desconto?", {"3", "6.2"}),
    ("que horas vocês abrem?", {"2"}),
    ("vocês abrem no sábado?", {"2"}),
    ("qual o endereço da loja?", {"1.2"}),
    ("qual o telefone de vocês?", {"1.2", "7"}),
    ("qual o whatsapp?", {"7", "1.2"}),
    ("me arrependi da compra, posso devolver?", {"4.1"}),
    ("o violão veio com defeito, posso trocar?", {"4.2"}),
    ("quero trocar por outra cor", {"4.3"}),
    ("quanto tempo tem de garantia?", {"8.1", "8.2"}),
    ("a entrega é grátis?", {"5.1"}),
    ("como funciona o envio para outra cidade?", {"5.2"}),
    ("onde vejo o código de rastreamento?", {"5.3"}),
    ("quando é a black friday?", {"6.1"}),
    ("o desconto do pix acumula com promoção?", {"6.2"}),
    ("vocês vendem corda de violão?", {"1"}),
    ("meus dados ficam seguros? como excluo?", {"9"}),
    ("em quanto tempo vocês respondem reclamação?", {"7.3", "7.1"}),
    ("e o prazo no whatsapp?", {"7.1"}),
]
# Written after the first 20, to check the first set was not tuned against.
SECOND_QUESTIONS = [
    ("tem parcelamento sem juros?", {"3", "3.1"}),
    ("aceita boleto?", {"3"}),
    ("quanto tempo demora a compensação do boleto", {"3"}),
    ("posso juntar pix com cartão para pagar?", {"3.1"}),
    ("se eu comprar e não gostar da cor, dá pra trocar?", {"4.3"}),
    ("o instrumento chegou riscado, e agora?", {"4.2", "5.2", "8.3"}),
    ("quem paga o frete se eu devolver?", {"4.1"}),
    ("vocês entregam em Dourados?", {"5.2"}),
    ("quanto é o frete aqui em Campo Grande?", {"5.1"}),
    ("em quantos dias chega em São Paulo?", {"5.2"}),
    ("que dias vocês têm promoção?", {"6.1"}),
    ("fecha no feriado?", {"2"}),
    ("funciona domingo?", {"2"}),
    ("a garantia cobre queda?", {"8.3", "4.2"}),
    ("vocês guardam meus dados pessoais?", {"9"}),
    ("quem é o dono da empresa, qual o CNPJ?", {"1.2"}),
    ("há quanto tempo a loja existe?", {"1", "1.2"}),
    ("a boquilha do sax pode trocar?", {"4.4"}),
]

POLICY_QUESTIONS = FIRST_QUESTIONS + SECOND_QUESTIONS


@pytest.fixture(scope="module")
def retriever() -> PolicyRetriever:
    embeddings: Embeddings = build_embeddings()
    try:
        return PolicyRetriever(load_policy_sections(), embeddings)
    except Exception as error:  # noqa: BLE001 - Ollama stopped or the model is not pulled
        pytest.skip(f"embeddings model unavailable: {type(error).__name__}")


def test_the_right_section_is_among_the_top_three_for_almost_every_question(
    retriever: PolicyRetriever,
):
    misses = [
        question
        for question, expected in POLICY_QUESTIONS
        if not expected & {hit.section.number for hit in retriever.retrieve(question)}
    ]

    # 37 of 38 when measured; the miss is a question about boleto compensation time.
    assert len(misses) <= 2, misses


def test_most_questions_have_the_right_section_first(retriever: PolicyRetriever):
    firsts = sum(
        retriever.retrieve(question)[0].section.number in expected
        for question, expected in POLICY_QUESTIONS
    )

    assert firsts / len(POLICY_QUESTIONS) >= 0.75
