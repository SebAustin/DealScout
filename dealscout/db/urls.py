"""Real marketplace search URLs for any make/model/location."""
import re
import unicodedata
from urllib.parse import quote_plus

from dealscout.db.geo import city_state, zip_for_location

# CarGurus entity IDs from /research/price-trends/ pages (make=m#, model=d#)
_CARGURUS_MAKES: dict[str, str] = {
    "tesla": "m112",
    "honda": "m6",
    "toyota": "m7",
    "bmw": "m3",       # NOT m19 — m19 is Audi
    "ford": "m2",
    "porsche": "m43",
    "lamborghini": "m34",
    "ferrari": "m132",
    "mclaren": "m196",
    "aston martin": "m5",
    "bentley": "m8",
    "maserati": "m22",
    "mercedes-benz": "m23",
    "mercedes": "m23",
    "audi": "m19",     # m19 → Audi on CarGurus
    "lexus": "m20",
    "jaguar": "m17",
    "land rover": "m18",
    "jeep": "m16",
    "chevrolet": "m1",
    "nissan": "m12",
}

_CARGURUS_MM: dict[tuple[str, str], str] = {
    ("tesla", "model 3"): "m112/d2475",
    ("tesla", "model y"): "m112/d3044",
    ("honda", "civic"): "m6/d404",
    ("toyota", "camry"): "m7/d292",
    ("bmw", "3 series"): "m3/d585",
    ("bmw", "x5"): "m3/d393",
    ("ford", "f-150"): "m2/d893",
    ("ford", "f150"): "m2/d893",
    ("porsche", "cayenne"): "m43/d823",
    ("porsche", "macan"): "m43/d1872",
    ("porsche", "911"): "m43/d582",
    ("porsche", "panamera"): "m43/d824",
    ("audi", "a4"): "m19/d586",
    ("audi", "q5"): "m19/d590",
    ("lamborghini", "huracan"): "m34/d2285",
    ("lamborghini", "urus"): "m34/d2787",
    ("lamborghini", "aventador"): "m34/d2284",
    ("ferrari", "488"): "m132/d2560",
    ("mclaren", "720s"): "m196/d3120",
}

# Common spelling variants → canonical model key
_MODEL_ALIASES: dict[str, str] = {
    "hurican": "huracan",
    "huracán": "huracan",
    "model3": "model 3",
    "modely": "model y",
    "f150": "f-150",
    "3series": "3 series",
    "x5": "x5",
}


def _norm(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    return text.lower().strip()


def _norm_model(model: str) -> str:
    key = _norm(model).replace("-", " ").replace("_", " ")
    key = re.sub(r"\s+", " ", key).strip()
    return _MODEL_ALIASES.get(key.replace(" ", ""), _MODEL_ALIASES.get(key, key))


def _lookup_mm_path(make: str, model: str) -> str | None:
    mk = _norm(make)
    md = _norm_model(model) if model else ""

    if md:
        for key in (md, md.split()[0]):
            path = _CARGURUS_MM.get((mk, key))
            if path:
                return path

    make_id = _CARGURUS_MAKES.get(mk)
    if make_id:
        return make_id
    return None


def cargurus_search(
    make: str,
    model: str,
    location: str,
    max_price: int | None = None,
    year: int | None = None,
    *,
    filter_year: bool = False,
) -> str:
    """CarGurus /search with makeModelTrimPaths (browse /Cars/... paths often 404)."""
    zip_code = zip_for_location(location)
    mm_path = _lookup_mm_path(make, model)

    if mm_path:
        enc = mm_path.replace("/", "%2F")
        url = f"https://www.cargurus.com/search?zip={zip_code}&distance=150&makeModelTrimPaths={enc}"
        if max_price:
            url += f"&maxPrice={int(max_price)}"
        # Demo browse links: do NOT pin to synthetic listing year (e.g. 2026 only)
        if filter_year and year:
            url += f"&minYear={year}&maxYear={year}"
        return url

    return autotrader_search(make, model, location, max_price)


def autotrader_search(
    make: str,
    model: str,
    location: str,
    max_price: int | None = None,
) -> str:
    city, state = city_state(location)
    city_s = city.lower().replace(" ", "-")
    state_s = state.lower() if len(state) == 2 else "us"
    make_s = _norm(make).replace(" ", "-")
    model_s = _norm_model(model).replace(" ", "-") if model else "all"
    url = (
        f"https://www.autotrader.com/cars-for-sale/{make_s}/{model_s}/{city_s}-{state_s}"
        f"?zip={zip_for_location(location)}"
    )
    if max_price:
        url += f"&maxPrice={int(max_price)}"
    return url


def craigslist_search(make: str, model: str, location: str) -> str:
    city = location.split(",")[0].strip().lower().replace(" ", "")
    if not city or city == "united-states":
        city = "sfbay"
    q = quote_plus(f"{make} {model}".strip() or "used car")
    return f"https://{city}.craigslist.org/search/cta?query={q}"


def demo_url(
    source: str,
    make: str,
    model: str,
    year: int,
    location: str,
    max_price: int | None = None,
) -> str:
    """Build a browse-similar URL — year on the demo card is not sent as a CarGurus filter."""
    src = (source or "").lower()
    if "cargurus" in src:
        return cargurus_search(make, model, location, max_price=max_price, filter_year=False)
    if "autotrader" in src:
        return autotrader_search(make, model, location, max_price)
    if "craigslist" in src:
        return craigslist_search(make, model, location)
    return autotrader_search(make, model, location, max_price)


def is_demo_placeholder(url: str) -> bool:
    if not url:
        return True
    return any(m in url for m in ("example-", "example.", "/example", "example-dealer"))


def is_stale_cargurus_url(url: str) -> bool:
    if "cargurus.com" not in (url or ""):
        return False
    if "searchQuery=" in url and "makeModelTrimPaths=" not in url:
        return True
    if "inventorylisting/viewDetailsFilterViewInventoryListing" in url:
        return True
    # Old browse-style paths that often show no results
    if re.search(r"cargurus\.com/Cars/[^/]+-l-", url):
        return True
    # Make-only path when model-specific path expected (legacy bad links)
    if "makeModelTrimPaths=m19&" in url and "d" not in url.split("makeModelTrimPaths=")[1].split("&")[0]:
        return True
    if re.search(r"minYear=20\d{2}&maxYear=20\d{2}", url):
        return True
    return False
