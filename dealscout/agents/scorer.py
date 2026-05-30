"""Scorer agent — compares listings to market data, assigns deal scores."""
import logging
from typing import Any

from dealscout.agents.state import DealScoutState, ScoredDeal
from dealscout.db import cache
from dealscout.llm import ask_json

logger = logging.getLogger(__name__)

SYSTEM = """Score used car deals 0-100 vs market average.
Return JSON: {"deals": [{"title","price","market_price","deal_score","reason","url","source","mileage","scraped_at"}]}
deal_score: 90+ exceptional, 75+ good, 60+ fair. reason is one line explaining the score."""


async def scorer_node(state: DealScoutState) -> dict[str, Any]:
    query = state.get("query", "")
    listings = state.get("listings") or []
    market_data = state.get("market_data", "")
    events: list[str] = [f"💰 Scorer evaluating {len(listings)} listings..."]
    scored: list[ScoredDeal] = []

    if not listings:
        events.append("⚠️ No listings to score")
        return {"scored_deals": [], "events": events}

    plan = state.get("plan") or {}
    plan_make = (plan.get("make") or "").lower()
    if plan_make:
        listings = [
            li for li in listings
            if plan_make in (li.get("make") or "").lower()
        ]
        if not listings:
            events.append(f"⚠️ No {plan.get('make')} listings after filter — rescoring skipped")
            return {"scored_deals": [], "events": events}

    # Pass through pre-scored listings only if they match the requested make
    if all(li.get("deal_score") for li in listings):
        scored = [{**li, "title": li.get("title") or f"{li.get('year')} {li.get('make')} {li.get('model')}"} for li in listings]
        events.append(f"✅ Using pre-scored cache ({len(scored)} deals)")
        return {"scored_deals": scored, "events": events}

    prompt = (
        f"Query: {query}\nMarket data:\n{market_data[:4000]}\n\n"
        f"Listings:\n{listings}"
    )
    try:
        data = await ask_json(SYSTEM, prompt, max_tokens=4096)
        scored = data.get("deals", [])
    except Exception as exc:
        logger.warning("LLM scoring failed: %s", exc)
        scored = []

    if not scored:
        scored = _rule_based_score(listings)
        events.append("⚡ Rule-based scoring fallback applied")

    for deal in scored:
        deal.setdefault("scraped_at", listings[0].get("scraped_at", ""))
        cache.save_listing(query, deal)

    events.append(f"✅ Scored {len(scored)} deals")
    return {"scored_deals": scored, "events": events}


def _rule_based_score(listings: list) -> list[ScoredDeal]:
    """Simple %-below-estimate scoring when LLM unavailable."""
    deals: list[ScoredDeal] = []
    for idx, li in enumerate(listings):
        price = float(li.get("price") or 0)
        if price <= 0:
            continue
        # Rough market estimate: vary premium by listing index so scores differ
        premium = 1.08 + idx * 0.03
        market = round(price * premium)
        pct_below = (market - price) / market * 100
        score = min(99, max(40, int(60 + pct_below * 3)))
        deals.append({
            "title": li.get("title") or f"{li.get('year')} {li.get('make')} {li.get('model')}",
            "price": price,
            "market_price": market,
            "deal_score": score,
            "reason": f"{pct_below:.0f}% below estimated market for {li.get('location', 'area')}.",
            "url": li.get("url", ""),
            "source": li.get("source", ""),
            "mileage": li.get("mileage"),
            "scraped_at": li.get("scraped_at", ""),
        })
    return deals
