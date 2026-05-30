# DealPulse Scout — Slide Deck

## View live (presenting)

Open in a browser:

```bash
open presentation/index.html
# or: python -m http.server 8765 --directory presentation
```

**Navigation:** Arrow keys, Space (next), Page Up/Down, Home/End.

## Export to PDF

### Option A — Script (headless Chrome)

```bash
./presentation/export-pdf.sh
```

Output: `presentation/DealPulse_Scout_Slides.pdf`

### Option B — Browser Print

1. Open `index.html` in Chrome or Edge
2. **Cmd+P** (Mac) or **Ctrl+P** (Windows)
3. Destination: **Save as PDF**
4. Layout: **Landscape**
5. Margins: **Default** or **Minimum**
6. Enable **Background graphics**
7. Save as `DealPulse_Scout_Slides.pdf`

Each slide prints as one landscape page (12 pages total).

## Contents

| Slide | Title |
|-------|-------|
| 1 | Title |
| 2 | The Problem |
| 3 | Our Solution |
| 4 | Architecture |
| 5 | Bright Data Integration |
| 6 | Claude AI Layer |
| 7 | Live Demo UI |
| 8 | Demo Walkthrough (BMW X5) |
| 9 | Demo vs Live Mode |
| 10 | Tech Stack |
| 11 | Limitations & Future Work |
| 12 | Thank You |

## Video recording

See [VIDEO_SCRIPT.md](VIDEO_SCRIPT.md) for timed narration, demo storyboard, and recording checklist.

## Customization

- **Screenshots:** Live captures in `screenshots/` (`app-home.png`, `app-results.png`, `app-deal-detail.png`). Re-capture after UI changes with Puppeteer/Chrome against a running `./run.sh` instance.
- **Colors:** Edit CSS variables in `styles.css` (`--accent`, `--bg`, etc.). Print/PDF uses high-contrast dark text on white.
