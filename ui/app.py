"""Streamlit demo UI for DealPulse Scout."""
import json
import os
import sys
from pathlib import Path

# Streamlit Cloud runs ui/app.py without repo root on sys.path
_ROOT = Path(__file__).resolve().parent.parent
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

import httpx
import streamlit as st

from db.urls import is_demo_placeholder

API_URL = os.getenv("API_URL", "http://localhost:8000")
DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"
EXPECTED_PIPELINE = "v2"

def _api_reachable() -> bool:
    try:
        r = httpx.get(f"{API_URL}/health", timeout=2.5)
        return r.status_code == 200
    except Exception:
        return False


def _sync_demo_mode() -> None:
    """Keep config.DEMO_MODE aligned with UI toggle / secrets."""
    import config
    config.DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"


def _embedded_search(q: str) -> tuple[list[str], list[dict]]:
    """Run LangGraph pipeline in-process (Streamlit Cloud / no FastAPI)."""
    import asyncio
    from agents.graph import run_search_stream

    _sync_demo_mode()
    logs: list[str] = []
    deals: list[dict] = []

    async def _run() -> None:
        nonlocal deals
        async for event in run_search_stream(q):
            if event.get("type") == "log":
                logs.append(event.get("message", ""))
            elif event.get("type") == "result":
                deals = event.get("deals", [])

    asyncio.run(_run())
    return logs, deals


st.set_page_config(page_title="DealPulse Scout", page_icon="🚗", layout="wide")
st.title("🚗 DealPulse Scout")
st.caption("LangGraph multi-agent car deal finder — powered by Bright Data + Claude")

query = st.text_input(
    "What are you looking for?",
    placeholder="e.g. Lamborghini Huracán Miami under 300k · Toyota Supra Los Angeles · BMW X5 Chicago",
    value="",
)

col1, col2 = st.columns([1, 4])
with col1:
    search_btn = st.button("🔍 Find Deals", type="primary", use_container_width=True)
with col2:
    demo = st.toggle("Demo mode (simulated deals)", value=True)
    if demo:
        os.environ["DEMO_MODE"] = "true"
    else:
        os.environ["DEMO_MODE"] = "false"

log_area = st.empty()
results_area = st.container()
USE_API = _api_reachable()


def render_deal(deal: dict):
    rank = deal.get("rank", "?")
    score = deal.get("deal_score", 0)
    color = "🟢" if score >= 85 else "🟡" if score >= 70 else "🔴"
    with st.expander(f"{color} #{rank} — {deal.get('title')} (Score: {score})", expanded=rank == 1):
        c1, c2, c3 = st.columns(3)
        c1.metric("Price", f"${deal.get('price', 0):,.0f}")
        c2.metric("Market Avg", f"${deal.get('market_price', 0):,.0f}")
        c3.metric("Mileage", f"{deal.get('mileage', 0):,} mi")
        st.info(deal.get("reason", ""))
        st.caption(f"Source: {deal.get('source')} · Scraped: {deal.get('scraped_at', '')[:19]}")
        url = deal.get("url")
        if url:
            demo_listing = DEMO_MODE or is_demo_placeholder(url) or "Demo sample" in (deal.get("reason") or "")
            label = f"Browse similar on {deal.get('source', 'site')} →" if demo_listing else "View Listing →"
            st.link_button(label, url)
            if demo_listing:
                st.caption(
                    "Demo mode: scores are simulated. Link opens live inventory matching this make/model — "
                    "not the exact VIN shown above."
                )


if search_btn and query:
    logs: list[str] = []
    deals: list[dict] = []

    with st.spinner("Agents working..."):
        use_api = USE_API
        if use_api:
            try:
                with httpx.stream(
                    "GET",
                    f"{API_URL}/search",
                    params={"q": query, "stream": "true"},
                    timeout=120.0,
                ) as resp:
                    resp.raise_for_status()
                    for line in resp.iter_lines():
                        if not line.startswith("data: "):
                            continue
                        event = json.loads(line[6:])
                        if event.get("type") == "log":
                            logs.append(event.get("message", ""))
                            log_area.code("\n".join(logs[-20:]), language=None)
                        elif event.get("type") == "result":
                            deals = event.get("deals", [])
                        elif event.get("type") == "error":
                            st.error(event.get("message"))
            except httpx.HTTPError:
                use_api = False

        if not use_api:
            logs, deals = _embedded_search(query)
            if logs:
                log_area.code("\n".join(logs[-20:]), language=None)

    with results_area:
        st.subheader("Top 3 Deals")
        if deals:
            for deal in deals:
                render_deal(deal)
        else:
            st.warning("No deals found. Include a brand in your query, e.g. Porsche Panamera Austin.")

elif search_btn:
    st.warning("Enter a search query first.")

with st.sidebar:
    st.header("Runtime")
    if USE_API:
        try:
            health = httpx.get(f"{API_URL}/health", timeout=3.0).json()
            pipeline = health.get("pipeline", "unknown")
            st.success(f"FastAPI online · pipeline **{pipeline}**")
            if pipeline != EXPECTED_PIPELINE:
                st.warning(f"Stale API (expected {EXPECTED_PIPELINE}). Restart `./run.sh`.")
        except Exception:
            st.info(f"Embedded pipeline **{EXPECTED_PIPELINE}** · demo mode")
    else:
        st.info(f"Embedded pipeline **{EXPECTED_PIPELINE}** · demo mode")
        st.caption(
            "Streamlit Cloud runs the LangGraph agents in-process. "
            "For FastAPI + SSE locally, use `./run.sh`."
        )

    st.header("Local setup")
    st.code("curl -s http://localhost:8000/health\n./run.sh", language="bash")
    st.markdown("**Stack:** LangGraph · Bright Data MCP · Claude · FastAPI · Streamlit")
