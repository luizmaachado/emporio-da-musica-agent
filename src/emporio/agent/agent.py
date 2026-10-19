"""Builds the customer service agent."""
from typing import Any

from langchain.agents import create_agent
from langchain.agents.middleware.types import AgentState
from langchain_core.language_models.chat_models import BaseChatModel
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph.state import CompiledStateGraph

from emporio.agent.prompt import SYSTEM_PROMPT
from emporio.agent.tools import build_tools
from emporio.data.loader import load_active_promotions, load_categories, load_products
from emporio.services.search import ProductSearchService

type Agent = CompiledStateGraph[AgentState[Any], None, Any, Any]


def build_agent(model: BaseChatModel) -> Agent:
    """Wire the store data, the tools and the prompt around `model`.

    This is the composition root: it loads the data and builds the services. The conversation
    history is kept in memory, per `thread_id`.
    """
    search = ProductSearchService(load_products(), load_categories(), load_active_promotions())
    return create_agent(
        model,
        build_tools(search),
        system_prompt=SYSTEM_PROMPT,
        checkpointer=InMemorySaver(),
    )
