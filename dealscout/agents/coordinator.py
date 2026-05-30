"""Coordinator agent — parses user query into a structured search plan."""
import logging
from typing import Any

from dealscout.agents.query_parse import parse_query
from dealscout.agents.state import DealScoutState, SearchPlan
from dealscout.llm import ask_json

logger = logging.getLogger(__name__)

SYSTEM = """You parse car deal search queries into structured JSON for ANY brand and ANY location worldwide.
Return ONLY valid JSON with keys:
make, model, year_min, year_max, max_price, location, keywords.

Rules:
- make: manufacturer (e.g. Porsche, Toyota, Lamborghini) — always extract if present
- model: specific model (e.g. Cayenne, Supra, Huracán) — empty string if not specified
- location: city and region (e.g. "Miami, FL", "London, UK", "Tokyo, JP")
- max_price: number in USD; parse "80k" as 80000
- keywords: cleaned version of the user query"""

SOURCES = [
    {"name": "CarGurus", "tool": "scraping_browser",
     "url_template": "https://www.cargurus.com/Cars/inventorylisting/viewDetailsFilterViewInventoryListing.action?search={keywords}"},
    {"name": "AutoTrader", "tool": "scraping_browser",
     "url_template": "https://www.autotrader.com/cars-for-sale/all-cars/{make}/{model}?zip={zip}"},
    {"name": "Craigslist", "tool": "web_unlocker",
     "url_template": "https://{city}.craigslist.org/search/cta?query={keywords}"},
]


async def coordinator_node(state: DealScoutState) -> dict[str, Any]:
    query = state.get("query", "")
    events = [f"🧭 Coordinator parsing: '{query}'"]

    plan_data = await ask_json(SYSTEM, query)
    heuristic = parse_query(query)
    if not plan_data:
        plan_data = heuristic
    else:
        # Merge: LLM wins, heuristic fills gaps
        for key, val in heuristic.items():
            if not plan_data.get(key) and val:
                plan_data[key] = val

    plan: SearchPlan = {
        "make": (plan_data.get("make") or "").strip(),
        "model": (plan_data.get("model") or "").strip(),
        "year_min": plan_data.get("year_min") or 2015,
        "year_max": plan_data.get("year_max") or 2026,
        "max_price": int(plan_data.get("max_price") or 50000),
        "location": plan_data.get("location") or "United States",
        "keywords": plan_data.get("keywords") or query,
    }
    label = f"{plan['make']} {plan['model']}".strip() or "any vehicle"
    events.append(
        f"📋 Plan: {label} near {plan.get('location')}, max ${plan.get('max_price'):,}"
    )
    logger.info("Search plan: %s", plan)
    return {"plan": plan, "events": events, "raw_scrapes": [], "listings": []}
