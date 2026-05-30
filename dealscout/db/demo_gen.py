"""Generate on-the-fly demo listings for any make/model/location."""
import hashlib
from datetime import datetime, timezone
from typing import Any

from dealscout.db.urls import demo_url

_SOURCES = ["CarGurus", "AutoTrader", "Craigslist"]
_TRIM_SUFFIXES = ["", "Premium", "Sport"]


def _price_tier(make: str, max_price: int) -> int:
    """Estimate base price from make name hash + budget (demo only)."""
    luxury_hints = (
        "porsche", "ferrari", "lamborghini", "maserati", "bentley", "rolls",
        "aston", "mclaren", "bugatti", "tesla", "bmw", "mercedes", "audi",
        "lexus", "cadillac", "genesis", "lincoln", "jaguar", "land rover",
    )
    mk = make.lower()
    if any(h in mk for h in luxury_hints):
        base = int(max_price * 0.72)
    else:
        base = int(max_price * 0.45)
    # Stable variation per brand
    jitter = int(hashlib.md5(mk.encode()).hexdigest()[:4], 16) % 5000
    return max(8000, min(base + jitter, max_price - 2000))


def _model_variants(make: str, model: str, limit: int) -> list[str]:
    if model:
        base = model.strip()
        variants = [base]
        for suffix in _TRIM_SUFFIXES[1:]:
            variants.append(f"{base} {suffix}".strip())
        # Year-ish trim labels for variety
        if len(variants) < limit:
            variants.append(f"{base} Limited")
        return variants[:limit]
    # Make-only: generic body styles work for any brand
    return ["Sedan", "SUV", "Coupe"][:limit]


def synthesize_listings(query: str, plan: dict, limit: int = 3) -> list[dict[str, Any]]:
    """Build plausible demo deals for any brand, model, and city."""
    make = (plan.get("make") or "").strip()
    if not make:
        make = _guess_make_from_query(query)

    model_plan = (plan.get("model") or "").strip()
    location = plan.get("location") or "United States"
    max_price = int(plan.get("max_price") or 50000)
    year_max = int(plan.get("year_max") or 2026)
    base = _price_tier(make, max_price)
    models = _model_variants(make, model_plan, limit)
    city_label = location.split(",")[0].strip()

    now = datetime.now(timezone.utc).isoformat()
    # Simulated % below market — decreases by rank so top deal scores highest
    discount_tiers = [14, 10, 7, 5]
    listings: list[dict[str, Any]] = []
    for i, model in enumerate(models):
        year = min(year_max, year_max - i)
        price = min(max_price - i * 3500, int(base * (1.0 - i * 0.05)))
        price = max(5000, price)
        mileage = 8000 + i * 12000
        pct = discount_tiers[i] if i < len(discount_tiers) else 5
        # Lower mileage / newer year nudge score up slightly (demo only)
        pct += max(0, 2 if mileage < 15000 else (-1 if mileage > 25000 else 0))
        pct = max(3, min(20, pct))
        market = int(round(price / (1 - pct / 100)))
        score = min(96, 72 + pct)
        source = _SOURCES[i % len(_SOURCES)]
        listings.append({
            "title": f"{year} {make} {model}".strip(),
            "make": make,
            "model": model,
            "year": year,
            "price": float(price),
            "market_price": float(market),
            "deal_score": float(score),
            "mileage": mileage,
            "location": location,
            "source": source,
            "reason": (
                f"{pct}% below estimated market for {make} {model} near {city_label}. "
                "(Demo sample — live mode scrapes real listings)"
            ),
            "url": demo_url(source, make, model, year, location, max_price=max_price),
            "scraped_at": now,
        })
    return listings


def _guess_make_from_query(query: str) -> str:
    from dealscout.agents.query_parse import parse_query
    return parse_query(query).get("make") or "Used"
