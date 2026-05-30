# Judge Runbook — 60 Seconds to a Working Demo

## 1. Start (15 s)

```bash
cd "Web Data Unlocked"    # repo root
./run.sh
```

Wait for:

- `DealPulse Scout API (demo pipeline v2) on :8000`
- Streamlit opens at **http://localhost:8501**

## 2. Verify (10 s)

Sidebar should show: **API online · pipeline v2**

Or in a terminal:

```bash
curl -s http://localhost:8000/health
# {"status":"ok","demo_mode":true,"pipeline":"v2"}
```

If pipeline is not `v2`, press Ctrl+C and run `./run.sh` again.

## 3. Search (20 s)

Click **Find Deals** with one of these queries:

| Query | What to expect |
|-------|----------------|
| `BMW X5 Austin under 75k` | 3 BMW X5 deals; scores ~88 / 82 / 79; CarGurus link with `m3/d393` |
| `Lamborghini Huracán Miami under 300k` | Lamborghini deals; CarGurus Huracán entity |
| `Porsche Panamera Austin under 120k` | Porsche-only results (not Tesla/other brands) |

Watch the **agent log** panel scroll: Coordinator → Scraper → Normalizer → Scorer → Ranker.

## 4. Click a link (15 s)

Expand deal #1 → click **Browse similar on CarGurus →**

- Opens live BMW (or requested make) inventory near the city
- Filtered by budget (`maxPrice`)
- **Not** the exact VIN in the card — demo synthesizes sample listings; links prove real inventory exists

## What Is Simulated vs Real

| Simulated (demo mode) | Real |
|-----------------------|------|
| Listing title, price, mileage, VIN | Marketplace search URLs |
| Deal scores and "market price" | CarGurus / AutoTrader / Craigslist pages |
| Agent pipeline flow and SSE logs | LangGraph + FastAPI architecture |

Set `DEMO_MODE=false` in `.env` and restart for live Bright Data scraping (requires API tokens).

## Quick API Test (no UI)

```bash
curl -N "http://localhost:8000/search?q=bmw+x5+austin+under+75k" | head -20
```

## Presentation

- Slides: `presentation/DealPulse_Scout_Slides.pdf`
- Video script: `presentation/VIDEO_SCRIPT.md`
