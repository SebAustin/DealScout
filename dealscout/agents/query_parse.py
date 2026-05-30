"""Parse any car search query into make, model, location, budget — no hardcoded brand list required."""
import re
from typing import Any

# Multi-word makes checked before single tokens
_KNOWN_MAKES: dict[str, str] = {
    "bmw": "BMW", "gmc": "GMC", "kia": "KIA", "ram": "RAM", "mini": "MINI",
    "fiat": "FIAT", "alfa romeo": "Alfa Romeo", "aston martin": "Aston Martin",
    "land rover": "Land Rover", "mercedes-benz": "Mercedes-Benz", "rolls-royce": "Rolls-Royce",
}
_MULTI_MAKES = [
    "mercedes-benz", "mercedes benz", "land rover", "alfa romeo", "aston martin",
    "rolls royce", "am general", "american motors",
]

# Common US / international city hints → normalized "City, ST/Country"
_CITY_ALIASES: dict[str, str] = {
    "austin": "Austin, TX", "dallas": "Dallas, TX", "houston": "Houston, TX",
    "san antonio": "San Antonio, TX", "miami": "Miami, FL", "orlando": "Orlando, FL",
    "tampa": "Tampa, FL", "atlanta": "Atlanta, GA", "chicago": "Chicago, IL",
    "detroit": "Detroit, MI", "phoenix": "Phoenix, AZ", "denver": "Denver, CO",
    "seattle": "Seattle, WA", "portland": "Portland, OR", "los angeles": "Los Angeles, CA",
    "la": "Los Angeles, CA", "san francisco": "San Francisco, CA", "sf": "San Francisco, CA",
    "san diego": "San Diego, CA", "boston": "Boston, MA", "new york": "New York, NY",
    "nyc": "New York, NY", "philadelphia": "Philadelphia, PA", "nashville": "Nashville, TN",
    "charlotte": "Charlotte, NC", "raleigh": "Raleigh, NC", "minneapolis": "Minneapolis, MN",
    "kansas city": "Kansas City, MO", "st louis": "St Louis, MO", "las vegas": "Las Vegas, NV",
    "salt lake city": "Salt Lake City, UT", "columbus": "Columbus, OH", "cleveland": "Cleveland, OH",
    "pittsburgh": "Pittsburgh, PA", "baltimore": "Baltimore, MD", "washington dc": "Washington, DC",
    "dc": "Washington, DC", "london": "London, UK", "paris": "Paris, FR",
    "toronto": "Toronto, ON", "vancouver": "Vancouver, BC", "montreal": "Montreal, QC",
    "dubai": "Dubai, AE", "berlin": "Berlin, DE", "sydney": "Sydney, AU",
}

_STOP = frozenset({
    "used", "new", "certified", "cpo", "car", "cars", "vehicle", "vehicles", "find",
    "search", "looking", "for", "with", "and", "the", "a", "an", "under", "below",
    "max", "less", "than", "around", "near", "in", "at", "within", "budget", "price",
    "mileage", "miles", "mi", "k", "km", "or", "any", "good", "deal", "deals", "cheap",
})

_US_STATE_RE = re.compile(
    r"\b(AL|AK|AZ|AR|CA|CO|CT|DE|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|"
    r"MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY)\b",
    re.I,
)


def parse_query(query: str) -> dict[str, Any]:
    """Heuristic parser — works offline for any brand/city."""
    q = query.strip()
    ql = q.lower()

    max_price = _extract_price(ql)
    location = _extract_location(q, ql)
    remainder = _strip_price_location(q, ql, location)

    make, model = _extract_make_model(remainder)
    model = _canonical_model(model)

    return {
        "make": make,
        "model": model,
        "location": location,
        "max_price": max_price,
        "keywords": query.strip(),
        "year_min": _extract_year_min(ql),
        "year_max": _extract_year_max(ql),
    }


def _canonical_model(model: str) -> str:
    fixes = {
        "hurican": "Huracan",
        "huracan": "Huracan",
        "urus": "Urus",
        "aventador": "Aventador",
        "model 3": "Model 3",
        "model y": "Model Y",
    }
    key = model.lower().strip()
    return fixes.get(key, model.title() if model else "")


def _extract_price(ql: str) -> int:
    for pat in [
        r"(?:under|below|max|less\s+than|<)\s*\$?\s*([\d,]+)\s*k?\b",
        r"\$\s*([\d,]+)\s*k?\s*(?:budget|max|or\s+less)?",
        r"\b([\d,]+)\s*k\s*(?:budget|max)?\b",
    ]:
        m = re.search(pat, ql)
        if m:
            val = int(m.group(1).replace(",", ""))
            return val * 1000 if val < 1000 else val
    return 50000


def _extract_location(q: str, ql: str) -> str:
    # Explicit: "Los Angeles, CA"
    m = re.search(r"([A-Za-z .'-]+,\s*[A-Z]{2})\b", q)
    if m:
        return _normalize_location(m.group(1).strip(" ,"), ql)

    # City alias anywhere in query (before "in Austin" regex — avoids "Austin" → "in under")
    for alias, full in sorted(_CITY_ALIASES.items(), key=lambda x: -len(x[0])):
        if re.search(rf"\b{re.escape(alias)}\b", ql):
            return full

    # Explicit: "in Miami", "near Austin TX" (word-boundary prepositions only)
    m = re.search(
        r"\b(?:in|near|around|within)\s+([A-Za-z .,'-]+?)(?:\s*,|\s+under|\s+below|\s+max|\s+\d|\s*$)",
        q,
        re.I,
    )
    if m:
        loc = m.group(1).strip(" ,")
        if loc.lower() not in {"under", "below", "max"}:
            return _normalize_location(loc, ql)

    st = _US_STATE_RE.search(q)
    if st:
        return f"United States, {st.group(1).upper()}"

    return "United States"


def _normalize_location(loc: str, ql: str) -> str:
    key = loc.lower().strip()
    if key in _CITY_ALIASES:
        return _CITY_ALIASES[key]
    if "," in loc:
        parts = [p.strip() for p in loc.split(",")]
        if len(parts[-1]) == 2:
            return f"{parts[0]}, {parts[-1].upper()}"
        return loc
    st = _US_STATE_RE.search(loc) or _US_STATE_RE.search(ql)
    if st:
        city = _US_STATE_RE.sub("", loc).strip() or loc
        return f"{city}, {st.group(1).upper()}"
    return loc.title()


def _strip_price_location(q: str, ql: str, location: str) -> str:
    text = q
    for pat in [
        r"(?:under|below|max|less\s+than|<)\s*\$?\s*[\d,]+\s*k?\b",
        r"\$\s*[\d,]+\s*k?\s*(?:budget|max)?",
        r"\b(?:in|near|around|within)\s+[A-Za-z .,'-]+",
    ]:
        text = re.sub(pat, " ", text, flags=re.I)
    city = location.split(",")[0].strip()
    if city.lower() in ql:
        text = re.sub(rf"\b{re.escape(city)}\b", " ", text, flags=re.I)
    for alias in _CITY_ALIASES:
        if alias in ql:
            text = re.sub(rf"\b{re.escape(alias)}\b", " ", text, flags=re.I)
    return re.sub(r"\s+", " ", text).strip()


def _extract_make_model(remainder: str) -> tuple[str, str]:
    if not remainder:
        return "", ""

    rl = remainder.lower()
    for mm in _MULTI_MAKES:
        if rl.startswith(mm):
            rest = remainder[len(mm):].strip()
            model = _clean_model(rest)
            make = mm.title().replace("Benz", "Benz")  # Mercedes-Benz handled below
            if "mercedes" in mm:
                make = "Mercedes-Benz"
            elif "land rover" in mm:
                make = "Land Rover"
            elif "alfa romeo" in mm:
                make = "Alfa Romeo"
            elif "aston martin" in mm:
                make = "Aston Martin"
            elif "rolls royce" in mm:
                make = "Rolls-Royce"
            else:
                make = _KNOWN_MAKES.get(mm, mm.title())
            return make, model

    tokens = remainder.split()
    # Drop leading year
    while tokens and re.fullmatch(r"20\d{2}|19\d{2}", tokens[0]):
        tokens.pop(0)
    if not tokens:
        return "", ""

    make = tokens[0].title()
    model = _clean_model(" ".join(tokens[1:]))
    make = _KNOWN_MAKES.get(make.lower(), make)
    return make, model


def _clean_model(text: str) -> str:
    words = [w for w in text.split() if w.lower() not in _STOP]
    return " ".join(words).strip()


def _extract_year_min(ql: str) -> int:
    m = re.search(r"(?:from|since|after)\s+(20\d{2}|19\d{2})", ql)
    return int(m.group(1)) if m else 2015


def _extract_year_max(ql: str) -> int:
    m = re.search(r"(?:before|until|up\s+to)\s+(20\d{2}|19\d{2})", ql)
    return int(m.group(1)) if m else 2026
