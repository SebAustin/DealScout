"""US city → ZIP and location helpers for marketplace deep links."""
import re

# Expandable lookup; unknown cities fall back to state hub ZIP
_CITY_ZIP: dict[str, str] = {
    "austin": "78701", "dallas": "75201", "houston": "77002", "san antonio": "78205",
    "miami": "33101", "orlando": "32801", "tampa": "33602", "atlanta": "30303",
    "chicago": "60601", "detroit": "48201", "phoenix": "85001", "denver": "80202",
    "seattle": "98101", "portland": "97201", "los angeles": "90001", "san francisco": "94102",
    "san diego": "92101", "boston": "02108", "new york": "10001", "philadelphia": "19102",
    "nashville": "37201", "charlotte": "28202", "raleigh": "27601", "minneapolis": "55401",
    "kansas city": "64101", "st louis": "63101", "las vegas": "89101", "salt lake city": "84101",
    "columbus": "43215", "cleveland": "44114", "pittsburgh": "15222", "baltimore": "21201",
    "washington": "20001", "round rock": "78664", "cedar park": "78613",
}

_STATE_ZIP: dict[str, str] = {
    "TX": "78701", "CA": "90001", "FL": "33101", "NY": "10001", "IL": "60601",
    "GA": "30303", "AZ": "85001", "CO": "80202", "WA": "98101", "MA": "02108",
    "PA": "19102", "OH": "43215", "MI": "48201", "NC": "28202", "TN": "37201",
    "NV": "89101", "OR": "97201", "MN": "55401", "MO": "64101", "DC": "20001",
    "NJ": "07102", "VA": "23219", "MD": "21201", "WI": "53202", "IN": "46204",
}


def zip_for_location(location: str) -> str:
    loc = (location or "").strip()
    city = loc.split(",")[0].strip().lower()
    if city in _CITY_ZIP:
        return _CITY_ZIP[city]
    m = re.search(r",\s*([A-Z]{2})\b", loc)
    if m and m.group(1) in _STATE_ZIP:
        return _STATE_ZIP[m.group(1)]
    return "10001"  # national fallback


def city_state(location: str) -> tuple[str, str]:
    parts = [p.strip() for p in (location or "United States").split(",")]
    city = parts[0].replace(" ", "-")
    if len(parts) > 1 and len(parts[1]) == 2:
        return city, parts[1].upper()
    if len(parts) > 1:
        return city, parts[1][:2].upper() if len(parts[1]) >= 2 else "US"
    return city, "US"
