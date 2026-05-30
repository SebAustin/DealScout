# DealPulse Scout

LangGraph multi-agent car deal finder for the **Web Data Unlocked** hackathon. Parses natural-language queries, scrapes listings via **Bright Data MCP**, scores deals with **Claude**, and streams agent progress over SSE.

**Pipeline v2** — dynamic demo synthesis for any make/model/city; live scraping when `DEMO_MODE=false`.

## Quick Start (judges)

```bash
# From repo root — one command
./dealscout/run.sh
```

Manual setup:

```bash
cd dealscout
python3.12 -m venv .venv && source .venv/bin/activate
pip install --index-url https://pypi.org/simple -r requirements.txt
pip install --index-url https://pypi.org/simple -e ..
cp .env.example .env
python serve_api.py   # Terminal 1
python serve_ui.py    # Terminal 2
```

Verify the API is running pipeline v2:

```bash
curl -s http://localhost:8000/health
# expect: {"status":"ok","demo_mode":true,"pipeline":"v2"}
```

If `pipeline` is missing or not `v2`, stop `./run.sh` (Ctrl+C) and restart — an old API process may still be on port 8000. `run.sh` kills port 8000 and starts uvicorn with `--reload`.

Open **http://localhost:8501** and try:

- `BMW X5 Austin under 75k`
- `Lamborghini Huracán Miami under 300k`
- `Porsche Panamera Austin under 120k`
- `Toyota Supra Los Angeles under 60k`

See [docs/JUDGES.md](docs/JUDGES.md) for a 60-second judge runbook.

## Architecture

```
User Query → Coordinator → Scraper → Normalizer → Scorer → Ranker → Top 3
                ↓              ↓
           Claude LLM    Bright Data MCP (live mode)
                         SERP, Browser, Unlocker
```

| Agent | Role |
|-------|------|
| **Coordinator** | Parses query into make / model / location / budget |
| **Scraper** | Demo: synthesizes listings; Live: Bright Data per source |
| **Normalizer** | Structured `{make, model, year, price, mileage, location, url}` |
| **Scorer** | 0–100 deal score + reason vs market data |
| **Ranker** | Returns top 3 by score |

Full details: [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)

## Demo Mode vs Live Mode

| | Demo (`DEMO_MODE=true`) | Live (`DEMO_MODE=false`) |
|---|-------------------------|---------------------------|
| **Listings** | Synthesized on-the-fly via `db/demo_gen.py` | Scraped via Bright Data MCP |
| **Scores** | Simulated tiered discounts (88 / 82 / 79 style) | Claude + SERP market comparison |
| **URLs** | Live inventory **search** links (CarGurus, AutoTrader, Craigslist) | Actual listing URLs when scraped |
| **Tokens** | Not required | `BRIGHT_DATA_TOKEN` + `ANTHROPIC_API_KEY` |

Demo mode does **not** use the SQLite cache as its hot path. The cache holds legacy seed data; pipeline v2 always synthesizes from the parsed search plan.

**Browse links in demo:** Each deal opens a real marketplace search filtered by make/model, ZIP, and budget — not the exact VIN shown. CarGurus uses `makeModelTrimPaths` entity IDs from `db/urls.py` (e.g. BMW X5 → `m3/d393`, not `m19` which is Audi).

**Streamlit demo toggle:** The sidebar toggle sets `DEMO_MODE` in the UI process only. The API reads `.env` at startup — edit `.env` and restart `./run.sh` to switch the backend to live mode.

## Bright Data Tools (live mode, priority order)

1. `search_engine` (SERP) — market price research
2. `scraping_browser` — JS-heavy sites (CarGurus, AutoTrader)
3. `scrape_as_markdown` / web unlocker — dealer sites, Craigslist
4. Structured scrapers where available

MCP endpoint: `https://mcp.brightdata.com/sse?token=YOUR_TOKEN`

## API

```bash
# SSE stream (default) — watch agent logs in real time
curl -N "http://localhost:8000/search?q=bmw+x5+austin+under+75k"

# JSON response
curl "http://localhost:8000/search?q=honda+civic&stream=false"
```

### Deal output format

```json
{
  "rank": 1,
  "title": "2026 BMW X5",
  "price": 58073,
  "market_price": 67352,
  "deal_score": 88,
  "reason": "16% below estimated market for BMW X5 near Austin. (Demo sample — live mode scrapes real listings)",
  "url": "https://www.cargurus.com/search?zip=78701&distance=150&makeModelTrimPaths=m3%2Fd393&maxPrice=75000",
  "source": "CarGurus",
  "mileage": 8000,
  "scraped_at": "2026-05-29T..."
}
```

## Env Vars

| Variable | Required | Description |
|----------|----------|-------------|
| `BRIGHT_DATA_TOKEN` | Live mode | Bright Data API token |
| `ANTHROPIC_API_KEY` | Live mode | Claude API key |
| `DEMO_MODE` | No | `true` = synthesized demo deals (default) |
| `API_URL` | No | Streamlit → API URL (default `http://localhost:8000`) |

## Project Layout

```
dealscout/
├── agents/          # LangGraph nodes (coordinator, scraper, normalizer, scorer, ranker)
├── tools/           # Bright Data MCP client
├── api/             # FastAPI + SSE
├── ui/              # Streamlit frontend
├── db/              # demo_gen, urls, geo, SQLite cache (legacy seed)
├── docs/            # Architecture + judge runbook
├── presentation/    # Slide deck (PDF) + video script
└── data/            # cache.db (auto-created)
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| Sidebar shows pipeline ≠ `v2` | Restart `./run.sh` (kills stale port 8000 process) |
| CarGurus opens Audi instead of BMW | Stale API or wrong entity ID — restart; BMW = `m3`, Audi = `m19` |
| URL has `minYear=2026&maxYear=2026` | Stale API — restart; demo links no longer pin year |
| All three scores identical | Stale API — restart; v2 uses tiered demo discounts |
| Streamlit toggle doesn't change behavior | API reads `.env` at startup — restart after editing `.env` |
| `ModuleNotFoundError: dealscout` | Run from repo root with `PYTHONPATH=.` or `pip install -e ..` |

## Hackathon Notes

- No Docker required — one-command setup via `./run.sh`
- Scraping errors are caught per-source; pipeline continues in live mode
- Live scrapes saved to SQLite with timestamp
- Files kept under ~200 lines per module for fast iteration

## Presentation Materials

- **Slide deck (PDF):** [presentation/DealPulse_Scout_Slides.pdf](presentation/DealPulse_Scout_Slides.pdf) — export with `./presentation/export-pdf.sh`
- **Slide source:** [presentation/index.html](presentation/index.html) — open in browser for live presenting
- **Video script:** [presentation/VIDEO_SCRIPT.md](presentation/VIDEO_SCRIPT.md) — timed narration + demo storyboard + recording checklist
