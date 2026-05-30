"""LangGraph StateGraph wiring for DealPulse Scout."""
import logging
from typing import Any, AsyncIterator

from langgraph.graph import END, StateGraph

from agents.coordinator import coordinator_node
from agents.normalizer import normalizer_node
from agents.ranker import ranker_node
from agents.scorer import scorer_node
from agents.scraper import scraper_node
from agents.state import DealScoutState
from config import DEMO_MODE

logger = logging.getLogger(__name__)

_graph = None


def build_graph() -> StateGraph:
    g = StateGraph(DealScoutState)
    g.add_node("coordinator", coordinator_node)
    g.add_node("scraper", scraper_node)
    g.add_node("normalizer", normalizer_node)
    g.add_node("scorer", scorer_node)
    g.add_node("ranker", ranker_node)
    g.set_entry_point("coordinator")
    g.add_edge("coordinator", "scraper")
    g.add_edge("scraper", "normalizer")
    g.add_edge("normalizer", "scorer")
    g.add_edge("scorer", "ranker")
    g.add_edge("ranker", END)
    return g


def get_compiled_graph():
    global _graph
    if _graph is None:
        _graph = build_graph().compile()
    return _graph


async def run_search(query: str) -> dict[str, Any]:
    """Run full pipeline and return final state."""
    graph = get_compiled_graph()
    result = await graph.ainvoke({
        "query": query,
        "demo_mode": DEMO_MODE,
        "events": [],
    })
    return result


async def run_search_stream(query: str) -> AsyncIterator[dict[str, Any]]:
    """Stream node outputs for SSE — yields event dicts."""
    graph = get_compiled_graph()
    async for chunk in graph.astream(
        {"query": query, "demo_mode": DEMO_MODE, "events": []},
        stream_mode="updates",
    ):
        for node_name, update in chunk.items():
            events = update.get("events", [])
            for ev in events:
                yield {"type": "log", "node": node_name, "message": ev}
            if node_name == "ranker" and update.get("top_deals"):
                yield {"type": "result", "deals": update["top_deals"]}
    yield {"type": "done"}
