"""Ranker agent — returns top 3 scored deals."""
from typing import Any

from agents.state import DealScoutState, ScoredDeal


async def ranker_node(state: DealScoutState) -> dict[str, Any]:
    scored = state.get("scored_deals") or []
    events: list[str] = ["🏆 Ranker selecting top 3 deals..."]

    sorted_deals = sorted(scored, key=lambda d: d.get("deal_score") or 0, reverse=True)
    top3: list[ScoredDeal] = []
    for i, deal in enumerate(sorted_deals[:3], 1):
        ranked = {**deal, "rank": i}
        top3.append(ranked)

    for d in top3:
        price = d.get("price") or 0
        events.append(
            f"  #{d['rank']} {d.get('title')} — ${price:,.0f} "
            f"(score {d.get('deal_score')})"
        )
    events.append(f"✅ Returning top {len(top3)} deals")
    return {"top_deals": top3, "events": events}
