"""FastAPI backend with SSE streaming /search endpoint."""
import json
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from agents.graph import run_search, run_search_stream
from config import DEMO_MODE
from db import cache

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

PIPELINE_VERSION = "v2"


@asynccontextmanager
async def lifespan(app: FastAPI):
    cache.init_db()
    cache.seed_demo_data()
    logger.info("DealPulse Scout API ready (pipeline=%s, DEMO_MODE=%s)", PIPELINE_VERSION, DEMO_MODE)
    yield


app = FastAPI(title="DealPulse Scout", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health():
    return {"status": "ok", "demo_mode": DEMO_MODE, "pipeline": PIPELINE_VERSION}


@app.get("/search")
async def search(
    q: str = Query(..., min_length=2, description="Car search query"),
    stream: bool = Query(True, description="SSE stream of agent progress"),
):
    if stream:
        return StreamingResponse(
            _sse_generator(q),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )
    result = await run_search(q)
    return {"query": q, "deals": result.get("top_deals", []), "events": result.get("events", [])}


async def _sse_generator(query: str):
    try:
        async for event in run_search_stream(query):
            yield f"data: {json.dumps(event)}\n\n"
    except Exception as exc:
        logger.exception("Search failed")
        yield f"data: {json.dumps({'type': 'error', 'message': str(exc)})}\n\n"
