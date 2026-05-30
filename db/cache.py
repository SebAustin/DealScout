"""SQLite cache for scraped listings + demo mode fallback."""
import json
import logging
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from config import DB_PATH, DEMO_MODE
from db.demo_gen import synthesize_listings
from db.urls import demo_url, is_demo_placeholder, is_stale_cargurus_url

logger = logging.getLogger(__name__)


def _connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS listings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                query TEXT NOT NULL,
                source TEXT,
                title TEXT,
                make TEXT,
                model TEXT,
                year INTEGER,
                price REAL,
                mileage INTEGER,
                location TEXT,
                url TEXT,
                market_price REAL,
                deal_score REAL,
                reason TEXT,
                raw_content TEXT,
                scraped_at TEXT NOT NULL
            )
        """)
        conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_listings_query ON listings(query)"
        )


def save_listing(query: str, listing: dict[str, Any]) -> None:
    now = datetime.now(timezone.utc).isoformat()
    with _connect() as conn:
        conn.execute(
            """INSERT INTO listings
               (query, source, title, make, model, year, price, mileage,
                location, url, market_price, deal_score, reason, raw_content, scraped_at)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                query,
                listing.get("source"),
                listing.get("title"),
                listing.get("make"),
                listing.get("model"),
                listing.get("year"),
                listing.get("price"),
                listing.get("mileage"),
                listing.get("location"),
                listing.get("url"),
                listing.get("market_price"),
                listing.get("deal_score"),
                listing.get("reason"),
                listing.get("raw_content"),
                listing.get("scraped_at", now),
            ),
        )


def get_cached_deals(query: str, limit: int = 20, plan: dict | None = None) -> list[dict[str, Any]]:
    """Return cached listings ranked by query relevance, then deal score."""
    keywords = [w.lower() for w in query.split() if len(w) > 2]
    plan = plan or {}
    plan_make = (plan.get("make") or "").lower()
    plan_model = (plan.get("model") or "").lower()

    with _connect() as conn:
        rows = conn.execute(
            "SELECT * FROM listings ORDER BY deal_score DESC, scraped_at DESC"
        ).fetchall()

    scored_rows: list[tuple[int, sqlite3.Row]] = []
    for row in rows:
        title = (row["title"] or "").lower()
        q = (row["query"] or "").lower()
        make = (row["make"] or "").lower()
        model = (row["model"] or "").lower()
        location = (row["location"] or "").lower()
        haystack = f"{title} {q} {make} {model} {location}"

        # When coordinator parsed a make/model, require make match (avoids Honda on Tesla search)
        if plan_make and plan_make not in make:
            continue
        if plan_model and plan_model.replace(" ", "") not in model.replace(" ", ""):
            continue

        relevance = 0
        if plan_make and plan_make in make:
            relevance += 4
        if plan_model and plan_model.replace(" ", "") in model.replace(" ", ""):
            relevance += 4
        for kw in keywords:
            if kw in haystack:
                relevance += 1

        if relevance > 0 or not keywords:
            scored_rows.append((relevance, row))

    scored_rows.sort(key=lambda x: (x[0], x[1]["deal_score"] or 0), reverse=True)

    results = [_row_to_deal(row) for _, row in scored_rows[:limit]]

    # Never backfill unrelated makes — synthesize demo listings instead
    if len(results) < limit and plan_make:
        synth = synthesize_listings(query, plan, limit=limit)
        seen = {r.get("url") or r.get("title") for r in results}
        for deal in synth:
            key = deal.get("url") or deal.get("title")
            if key not in seen:
                results.append(deal)
                seen.add(key)
            if len(results) >= limit:
                break
    elif len(results) < limit and not plan_make:
        # No make in plan — backfill from cache by score only
        seen = {r.get("url") or r.get("title") for r in results}
        for row in rows:
            deal = _row_to_deal(row)
            key = deal.get("url") or deal.get("title")
            if key not in seen:
                results.append(deal)
                seen.add(key)
            if len(results) >= limit:
                break
    return results


def get_demo_top3(query: str) -> list[dict[str, Any]] | None:
    if not DEMO_MODE:
        return None
    deals = get_cached_deals(query, limit=3)
    if len(deals) >= 3:
        return _rank(deals[:10])[:3]
    seed_demo_data()
    deals = get_cached_deals(query, limit=3)
    return _rank(deals)[:3] if deals else None


def _row_to_deal(row: sqlite3.Row) -> dict[str, Any]:
    return {
        "title": row["title"],
        "price": row["price"],
        "market_price": row["market_price"],
        "deal_score": row["deal_score"],
        "reason": row["reason"],
        "url": row["url"],
        "source": row["source"],
        "mileage": row["mileage"],
        "scraped_at": row["scraped_at"],
        "make": row["make"],
        "model": row["model"],
        "year": row["year"],
        "location": row["location"],
    }


def _rank(deals: list[dict]) -> list[dict]:
    sorted_deals = sorted(deals, key=lambda d: d.get("deal_score") or 0, reverse=True)
    for i, d in enumerate(sorted_deals, 1):
        d["rank"] = i
    return sorted_deals


def seed_demo_data() -> None:
    """Pre-populate cache so demo never fails."""
    expected = 7
    with _connect() as conn:
        stale = conn.execute(
            "SELECT COUNT(*) FROM listings WHERE url LIKE '%example%'"
        ).fetchone()[0]
        rows = conn.execute("SELECT url FROM listings").fetchall()
        stale += sum(1 for r in rows if is_stale_cargurus_url(r["url"]))
        count = conn.execute("SELECT COUNT(*) FROM listings").fetchone()[0]
        unique = conn.execute(
            "SELECT COUNT(DISTINCT title || '|' || make || '|' || model) FROM listings"
        ).fetchone()[0]
        tesla_n = conn.execute(
            "SELECT COUNT(*) FROM listings WHERE lower(make)='tesla' AND lower(model) LIKE '%model 3%'"
        ).fetchone()[0]
        if count == expected and unique == expected and tesla_n == 3 and stale == 0:
            return
        conn.execute("DELETE FROM listings")
    now = datetime.now(timezone.utc).isoformat()
    demos = [
        {"query": "tesla model 3 austin", "source": "CarGurus", "title": "2022 Tesla Model 3 Long Range",
         "make": "Tesla", "model": "Model 3", "year": 2022, "price": 27500, "mileage": 28400,
         "location": "Austin, TX",
         "market_price": 30200, "deal_score": 91,
         "reason": "9% below market average for this trim/mileage in Austin. (Demo sample listing)"},
        {"query": "tesla model 3 austin", "source": "AutoTrader", "title": "2021 Tesla Model 3 Standard Range",
         "make": "Tesla", "model": "Model 3", "year": 2021, "price": 24800, "mileage": 35200,
         "location": "Round Rock, TX",
         "market_price": 26500, "deal_score": 84,
         "reason": "6% under market; higher mileage offset by price drop. (Demo sample listing)"},
        {"query": "tesla model 3 austin", "source": "CarGurus", "title": "2023 Tesla Model 3 RWD",
         "make": "Tesla", "model": "Model 3", "year": 2023, "price": 28900, "mileage": 19500,
         "location": "Cedar Park, TX",
         "market_price": 31200, "deal_score": 87,
         "reason": "7% below market; low mileage 2023 RWD in Cedar Park. (Demo sample listing)"},
        {"query": "honda civic used", "source": "CarGurus", "title": "2020 Honda Civic EX",
         "make": "Honda", "model": "Civic", "year": 2020, "price": 18900, "mileage": 41000,
         "location": "Dallas, TX",
         "market_price": 20500, "deal_score": 88,
         "reason": "8% below KBB fair purchase price for Dallas metro. (Demo sample listing)"},
        {"query": "bmw 3 series", "source": "AutoTrader", "title": "2019 BMW 330i xDrive",
         "make": "BMW", "model": "3 Series", "year": 2019, "price": 26500, "mileage": 52000,
         "location": "Houston, TX",
         "market_price": 29000, "deal_score": 79,
         "reason": "Certified pre-owned at 9% discount vs regional average. (Demo sample listing)"},
        {"query": "toyota camry", "source": "Craigslist", "title": "2021 Toyota Camry SE",
         "make": "Toyota", "model": "Camry", "year": 2021, "price": 21500, "mileage": 38000,
         "location": "San Antonio, TX",
         "market_price": 23400, "deal_score": 86,
         "reason": "Private party listing 8% under dealer average. (Demo sample listing)"},
        {"query": "ford f150", "source": "AutoTrader", "title": "2020 Ford F-150 XLT",
         "make": "Ford", "model": "F-150", "year": 2020, "price": 32900, "mileage": 45000,
         "location": "Austin, TX",
         "market_price": 35500, "deal_score": 82,
         "reason": "7% below market for crew cab XLT trim in Texas. (Demo sample listing)"},
    ]
    for d in demos:
        d["url"] = demo_url(d["source"], d["make"], d["model"], d["year"], d["location"])
        d["scraped_at"] = now
        save_listing(d["query"], d)
    logger.info("Seeded %d demo listings with live search URLs", len(demos))
