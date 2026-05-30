"""LangGraph state definition for DealPulse Scout."""
import operator
from typing import Annotated, TypedDict


class SearchPlan(TypedDict, total=False):
    make: str
    model: str
    year_min: int
    year_max: int
    max_price: int
    location: str
    keywords: str


class RawScrape(TypedDict, total=False):
    source: str
    url: str
    content: str
    error: str


class Listing(TypedDict, total=False):
    make: str
    model: str
    year: int
    price: float
    mileage: int
    location: str
    url: str
    title: str
    source: str
    scraped_at: str


class ScoredDeal(TypedDict, total=False):
    rank: int
    title: str
    price: float
    market_price: float
    deal_score: float
    reason: str
    url: str
    source: str
    mileage: int
    scraped_at: str


class DealScoutState(TypedDict, total=False):
    query: str
    plan: SearchPlan
    raw_scrapes: list[RawScrape]
    listings: list[Listing]
    market_data: str
    scored_deals: list[ScoredDeal]
    top_deals: list[ScoredDeal]
    events: Annotated[list[str], operator.add]
    demo_mode: bool
