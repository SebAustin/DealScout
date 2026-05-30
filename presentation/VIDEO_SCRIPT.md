# DealPulse Scout — Video Script

**Target length:** ~4 minutes  
**Audience:** Hackathon judges (Web Data Unlocked)  
**Format:** Screen recording + optional voiceover using this script

---

## Pre-Recording Checklist

- [ ] Close unrelated apps; enable Do Not Disturb
- [ ] Terminal + browser at 1080p or 1440p; zoom 100–125%
- [ ] Mic test — quiet room, pop filter if available
- [ ] Run `./run.sh` from repo root **before** hitting Record
- [ ] Verify sidebar: **API online · pipeline v2**
- [ ] Have these tabs ready: Streamlit (`localhost:8501`), terminal, optional CarGurus
- [ ] Optional: drop screenshots into slide 7 placeholder before recording B-roll

### Tools

- **OBS Studio** or **Loom** — full screen or window capture
- **QuickTime** (macOS) — File → New Screen Recording
- Export: MP4, H.264, 1080p, 30fps

### Fallback if live demo fails

- Show slide deck PDF (`DealPulse_Scout_Slides.pdf`) slides 7–8
- Run: `curl -N "http://localhost:8000/search?q=bmw+x5+austin+under+75k" | head -30`
- Narrate from the "Fallback" column below

---

## Script

| Time | Slide | Narration | On-screen action |
|------|-------|-----------|------------------|
| **0:00–0:20** | 1–2 | "Hi — I'm presenting DealPulse Scout, built for the Web Data Unlocked hackathon. Buying a used car means jumping between CarGurus, AutoTrader, Craigslist, and dealer sites. There's no single place that answers: what's the best deal near me, under my budget, with an explained score. That's what we built." | Title slide → Problem slide (or cut straight to Streamlit at 0:15) |
| **0:20–0:40** | 3 | "You type a natural-language query — any brand, any city, any budget. Our LangGraph pipeline returns the top three ranked deals with scores, reasons, and links to real inventory." | Show slide 3 or Streamlit search box empty |
| **0:40–1:50** | 7–8 | "Let me show you. I'll search: BMW X5 Austin under seventy-five K." | Type query → click **Find Deals** |
| | | "Watch the agent log — Coordinator parses the query, Scraper prepares listings, Normalizer structures them, Scorer assigns deal scores, Ranker picks the top three." | Point at scrolling log panel |
| | | "Here are three BMW X5 deals — ranked eighty-eight, eighty-two, and seventy-nine. Each card shows price, estimated market average, mileage, and a one-line reason." | Expand deal #1, then #2 briefly |
| | | "These are demo-mode sample listings — but the links are real. Click Browse on CarGurus…" | Click CarGurus link |
| | | "…and you get live BMW X5 inventory near Austin, filtered under seventy-five thousand dollars. The URL uses CarGurus entity IDs — m3 slash d393 for BMW X5 — not a hardcoded fake page." | Show CarGurus results tab; optionally highlight URL bar |
| **1:50–2:30** | 4–5 | "Under the hood: five LangGraph agents in sequence. In live mode, the Scraper calls Bright Data MCP — SERP for market research, Scraping Browser for JavaScript sites like CarGurus, and Web Unlocker for Craigslist and dealer pages. We didn't build proxy infrastructure — we plugged into Bright Data's MCP endpoint." | Slides 4–5 or split-screen architecture diagram |
| **2:30–3:00** | 6 | "Claude handles query parsing, listing extraction from raw HTML, and deal scoring against market data. If the LLM is unavailable, heuristic fallbacks keep the demo running — important for a live hackathon stage." | Slide 6 |
| **3:00–3:30** | 9 | "Demo mode synthesizes listings so judges always get a result without API keys. Live mode — set DEMO_MODE false in dot-env — scrapes real pages and scores with Claude. Same pipeline, same UI." | Slide 9; optional: `curl -s localhost:8000/health` showing pipeline v2 |
| **3:30–3:50** | 11 | "Limitations: we map about twenty CarGurus make-model entity IDs; unknown brands fall back to make-only search. Demo cards aren't exact VINs — they're proof that real inventory exists for your query." | Slide 11 |
| **3:50–4:00** | 12 | "One command to run it: `./run.sh`. Thanks — happy to take questions." | Slide 12 or terminal with run.sh |

---

## Optional Second Query (if time allows, +30 s)

| Time | Narration | On-screen |
|------|-----------|-----------|
| +0:00 | "It works for any brand — not just BMW." | Clear search box |
| +0:05 | "Lamborghini Huracán Miami under three hundred K." | Type → Find Deals |
| +0:20 | "Same pipeline — Lamborghini results, CarGurus Huracán entity, Miami ZIP." | Show top deal + link |

---

## B-Roll Shot List

1. `./run.sh` starting — terminal output "pipeline v2"
2. `curl -s http://localhost:8000/health` JSON response
3. Streamlit sidebar health check (green, pipeline v2)
4. Agent log scrolling during search
5. Three deal expanders with different scores (88 / 82 / 79)
6. CarGurus tab — BMW X5 listings near Austin
7. URL bar close-up: `makeModelTrimPaths=m3%2Fd393`
8. SSE curl output (optional technical B-roll)

---

## Fallback Narration (demo broken)

> "The API runs on FastAPI with Server-Sent Events — each agent node emits log lines you can see here in the terminal output. The final event contains the top three deals JSON. The architecture is LangGraph with Bright Data MCP for live scraping and Claude for scoring. Run `./run.sh` to try it locally."

Show: `curl -N "http://localhost:8000/search?q=bmw+x5+austin+under+75k"` output + slides PDF.

---

## Slide Sync Reference

| Slide | Topic |
|-------|-------|
| 1 | Title |
| 2 | Problem |
| 3 | Solution |
| 4 | Architecture |
| 5 | Bright Data |
| 6 | Claude |
| 7 | Demo UI (screenshot) |
| 8 | BMW X5 walkthrough |
| 9 | Demo vs Live |
| 10 | Tech stack |
| 11 | Limitations |
| 12 | Thank you / run command |

---

## Post-Production Notes

- Trim dead air before/after demo clicks
- Add lower-third once: "DealPulse Scout · Web Data Unlocked"
- Target export: **MP4, 1080p, under 100 MB** for submission portals
- Keep raw recording as backup
