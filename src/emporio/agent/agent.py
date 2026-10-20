"""Builds the customer service agent."""
from collections.abc import Sequence
from typing import Any

from langchain.agents import create_agent
from langchain.agents.middleware import ModelRequest, dynamic_prompt
from langchain.agents.middleware.types import AgentState
from langchain_core.embeddings import Embeddings
from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.state import CompiledStateGraph

from emporio.agent.policies import (
    DEFAULT_MIN_SCORE,
    DEFAULT_TOP_K,
    PolicyRetriever,
    prompt_with_policies,
)
from emporio.agent.prompt import SYSTEM_PROMPT
from emporio.agent.tools import build_tools
from emporio.data.loader import load_active_promotions, load_categories, load_products
from emporio.data.policies import load_policy_sections
from emporio.domain.policies import PolicySection
from emporio.services.payment import PaymentService
from emporio.services.search import ProductSearchService

type Agent = CompiledStateGraph[AgentState[Any], None, Any, Any]


def build_agent(
    model: BaseChatModel,
    embeddings: Embeddings,
    sections: Sequence[PolicySection] | None = None,
    *,
    policy_top_k: int = DEFAULT_TOP_K,
    policy_min_score: float | None = DEFAULT_MIN_SCORE,
) -> Agent:
    """Wire the store data, the manual, the tools and the prompt around `model`.

    This is the composition root: it loads the data, builds the services and embeds the manual
    sections once. `sections` defaults to the customer-facing sections of the manual; pass them
    in to share a single reading of the PDF. The conversation history is kept in memory, per
    `thread_id`.
    """
    products, promotions = load_products(), load_active_promotions()
    search = ProductSearchService(products, load_categories(), promotions)
    payment = PaymentService(products, promotions)
    policies = PolicyRetriever(
        load_policy_sections() if sections is None else sections,
        embeddings,
        top_k=policy_top_k,
        min_score=policy_min_score,
    )

    @dynamic_prompt
    def system_prompt(request: ModelRequest) -> str:
        return prompt_with_policies(SYSTEM_PROMPT, policies, request.state["messages"])

    return create_agent(
        model,
        build_tools(search, payment),
        middleware=[system_prompt],
        checkpointer=InMemorySaver(),
    )
