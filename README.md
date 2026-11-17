# ✦ SPACE MINER AI

**Mission 01 — The Hidden Ore Galaxy**: learn machine learning by training a real K-nearest-neighbors (KNN) classifier and making mining decisions under limited resources.

## NEW: V0.2 browser game (recommended)

The new interface includes a clickable galaxy map, visual planet selection, discovery zoom animation, KNN recommendations, hidden-label-safe API, and a Builder Mode for learning the math. **Python remains the sole source of actual KNN predictions.**

Requires Python 3.10+.

```powershell
# From the repository root
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt -r requirements-web.txt
python -m uvicorn webapp.server:app --reload
```

Open **http://127.0.0.1:8000** in your browser.

macOS/Linux activation: `source .venv/bin/activate`.

### First-time mission walkthrough

1. Press **Launch Expedition** and leave **K=3** selected.
2. Press **Train AI**. Blue-glowing planets are predicted to have ore; purple-glowing planets are predicted empty.
3. Click a blue planet. See its prediction and how many nearest training examples voted for ore.
4. Press **Mine & Reveal**. A zoom animation permanently reveals the true answer and updates credits.
5. Consider changing K or scanning new training-sector examples for 5 credits. Compare held-out validation accuracy and see whether the strategy improves.
6. After five mines, compare your score and retry the same seeded galaxy.

**Important:** A 2/3 ore vote is a majority classification, **not a 66.7% calibrated probability**, and the mined planet could still be empty. "Heat" and "Spectrum" are fictional sensor measurements, *not physical positions in space*.

### V0.2 architecture

- `webapp/server.py` — FastAPI mission-state API. Handles scan/train/mine. Keeps hidden ore labels server-side.
- `webapp/static/index.html` — mission screen and educational overlays.
- `webapp/static/styles.css` — responsive space-map theme and reveal animation.
- `webapp/static/game.js` — browser interactions and API calls (no KNN calculations).
- `space_miner/core.py` and `space_miner/strategy.py` — shared game engine and model logic.
- `tests/test_web_api.py` — server-side testing of score, permissions, session isolation, and hidden-label integrity.

This is a **local educational prototype**. Sessions exist in memory and vanish on server restart. It is not ready for public hosting without security, persistence, session limits and user authentication.

## Original Streamlit version (still available)

```powershell
python -m pip install -r requirements.txt
streamlit run app.py
```

## Run all Python tests

```powershell
python -m pytest -q
```

## Learning goals

CJAIO-aligned introductory material: Python, data representations, Euclidean distance, sorting, nearest-neighbor classification, training vs evaluation datasets, baselines, and analyzing prediction errors. The game does not replace independent Olympiad practice.

---
