"""Normalizer agent — extracts structured listing fields from raw scrapes."""
import logging
from datetime import datetime, timezone
from typing import Any

from agents.query_parse import parse_query
from agents.state import DealScoutState, Listing
from config import DEMO_MODE
from db.demo_gen import synthesize_listings
from llm import ask_json

logger = logging.getLogger(__name__)

SYSTEM = """Extract car listings from scraped web content.
Return JSON: {"listings": [{"make","model","year","price","mileage","location","url","title","source"}]}
price and mileage must be numbers. Skip invalid entries. Max 5 listings per source."""


async def normalizer_node(state: DealScoutState) -> dict[str, Any]:
    query = state.get("query", "")
    raw_scrapes = state.get("raw_scrapes") or []
    events: list[str] = ["🔧 Normalizer extracting structured listings..."]
    listings: list[Listing] = []
    now = datetime.now(timezone.utc).isoformat()

    if DEMO_MODE or state.get("demo_mode"):
        plan = dict(state.get("plan") or {})
        if not plan.get("make"):
            plan.update({k: v for k, v in parse_query(query).items() if v})
        if plan.get("make"):
            listings = synthesize_listings(query, plan, limit=3)
            events.append(
                f"✅ Generated {len(listings)} demo listings for "
                f"{plan['make']} {plan.get('model', '')}".strip()
            )
            return {"listings": listings, "plan": plan, "events": events}
        events.append('⚠️ Could not detect a brand — try e.g. "Porsche Panamera Austin"')
        return {"listings": [], "plan": plan, "events": events}

    for scrape in raw_scrapes:
        if scrape.get("error") or not scrape.get("content"):
            continue
        source = scrape.get("source", "unknown")
        prompt = (
            f"Source: {source}\nURL: {scrape.get('url', '')}\n\n"
            f"Content:\n{scrape['content'][:8000]}"
        )
        try:
            data = await ask_json(SYSTEM, prompt, max_tokens=2048)
            for item in data.get("listings", []):
                item["source"] = item.get("source") or source
                item["url"] = item.get("url") or scrape.get("url", "")
                item["scraped_at"] = now
                if item.get("price"):
                    listings.append(item)
        except Exception as exc:
            logger.warning("Normalize failed for %s: %s", source, exc)
            events.append(f"⚠️ Normalize skip {source}: {exc}")

    # Heuristic fallback if LLM returned nothing
    if not listings:
        listings = _heuristic_extract(raw_scrapes, now)
        events.append(f"⚡ Heuristic fallback: {len(listings)} listings")

    events.append(f"✅ Normalized {len(listings)} total listings")
    return {"listings": listings, "events": events}


def _heuristic_extract(scrapes: list, scraped_at: str) -> list[Listing]:
    """Minimal regex-free fallback — demo-safe placeholder listings."""
    results: list[Listing] = []
    for i, s in enumerate(scrapes):
        if s.get("content") and not s.get("error"):
            results.append({
                "title": f"Used vehicle listing #{i + 1}",
                "make": "Unknown",
                "model": "Unknown",
                "year": 2020,
                "price": 25000 - i * 1500,
                "mileage": 40000 + i * 5000,
                "location": "TX",
                "url": s.get("url", ""),
                "source": s.get("source", "web"),
                "scraped_at": scraped_at,
            })
    return results[:5]
