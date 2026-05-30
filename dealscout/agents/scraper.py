"""Scraper agent — calls Bright Data MCP tools per source."""
import logging
from datetime import datetime, timezone
from typing import Any
from urllib.parse import quote_plus

from dealscout.agents.coordinator import SOURCES
from dealscout.agents.query_parse import parse_query
from dealscout.agents.state import DealScoutState, RawScrape
from dealscout.config import DEMO_MODE
from dealscout.db.demo_gen import synthesize_listings
from dealscout.tools import brightdata_mcp

logger = logging.getLogger(__name__)


def _build_search_urls(plan: dict) -> list[tuple[str, str, str]]:
    """Return (source_name, tool_alias, url) tuples."""
    kw = quote_plus(plan.get("keywords", "used cars"))
    make = (plan.get("make") or "cars").lower().replace(" ", "-")
    model = (plan.get("model") or "").lower().replace(" ", "-")
    city = (plan.get("location") or "austin").split(",")[0].strip().lower().replace(" ", "")
    urls = []
    for src in SOURCES:
        url = src["url_template"].format(
            keywords=kw, make=make, model=model or "all", zip="78701", city=city
        )
        urls.append((src["name"], src["tool"], url))
    return urls


async def scraper_node(state: DealScoutState) -> dict[str, Any]:
    query = state.get("query", "")
    plan = state.get("plan") or {}
    events: list[str] = ["🔍 Scraper starting multi-source fetch..."]
    raw_scrapes: list[RawScrape] = []

    if DEMO_MODE or state.get("demo_mode"):
        plan = _resolve_plan(state)
        events.append("⚡ DEMO_MODE — generating listings from search plan")
        if plan.get("make"):
            synth = synthesize_listings(query, plan, limit=3)
            for c in synth:
                raw_scrapes.append({
                    "source": c.get("source", "demo"),
                    "url": c.get("url", ""),
                    "content": str(c),
                })
            events.append(
                f"✅ Prepared {len(raw_scrapes)} demo listings for "
                f"{plan['make']} {plan.get('model', '')}".strip()
            )
        else:
            events.append("⚠️ No make detected — add a brand to your query")
        return {"raw_scrapes": raw_scrapes, "plan": plan, "events": events}

    # Market data via SERP first
    market_query = (
        f"{plan.get('make', '')} {plan.get('model', '')} average used price "
        f"{plan.get('location', '')} {datetime.now().year}"
    ).strip()
    events.append(f"📊 SERP market lookup: {market_query}")
    try:
        market_data = await brightdata_mcp.web_search(market_query)
    except Exception as exc:
        logger.exception("SERP failed")
        market_data = f"[error] {exc}"
        events.append(f"⚠️ SERP failed, continuing: {exc}")
    else:
        events.append("✅ Market data retrieved")

    for source, tool_alias, url in _build_search_urls(plan):
        events.append(f"🌐 Scraping {source} via {tool_alias}...")
        try:
            if tool_alias == "scraping_browser":
                content = await brightdata_mcp.browser_scrape(url)
            else:
                content = await brightdata_mcp.scrape_url(url, tool_alias)
            if content.startswith("[error]"):
                raise RuntimeError(content)
            raw_scrapes.append({"source": source, "url": url, "content": content[:15000]})
            events.append(f"✅ {source}: {len(content)} chars scraped")
        except Exception as exc:
            logger.warning("Scrape failed for %s: %s", source, exc)
            raw_scrapes.append({"source": source, "url": url, "content": "", "error": str(exc)})
            events.append(f"⚠️ {source} skipped: {exc}")

    return {"raw_scrapes": raw_scrapes, "market_data": market_data, "events": events}


def _resolve_plan(state: DealScoutState) -> dict:
    plan = dict(state.get("plan") or {})
    if not plan.get("make"):
        parsed = parse_query(state.get("query", ""))
        for k, v in parsed.items():
            if v and not plan.get(k):
                plan[k] = v
    return plan
