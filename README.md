# ✦ SPACE MINER AI

## V0.7 — Visible version, reliable tabs, and measurable AI learning

**Branch:** `feat/playable-v0-7`, based on V0.6. Older versions remain unchanged for A/B comparison.

### What changed
- A **V0.7** release badge appears at the top-left of the game and on the launch dialog. The server health endpoint reports `0.7.0`. Each future update should increment the displayed release number.
- **Explore Galaxy**, **Train AI**, and **Missions & Results** are now three real, static, top-level HTML pages. They no longer depend on JavaScript moving an older single-column layout into tab containers. Tabs are sticky near the top.
- Asset URLs include a new version query string to refresh old browser-cached JavaScript and CSS.
- The novice AI begins with **severely biased** real training data (7 ore-region examples versus 1 empty-region example). The six reserve reports emphasize the underrepresented empty region. Unmined labels are never leaked or rewritten.
- The **Train AI** tab shows *accuracy* and *ORE precision* both before and after scanning new data; it also shows how many model predictions change. Precision means: of all planets predicted ORE on the held-out evaluation set, how many actually had ore?

### Reproducible default example
With seed 12, K=3 and Balanced sensors on 20 held-out validation planets:

| Model | Training examples | Accuracy | ORE precision |
|---|---:|---:|---:|
| Initial, incomplete | 8 | **35%** | **35%** |
| After verifying all six new reports | 14 | **85%** | **75%** |

The AI has not been randomly sabotaged: this is a deliberately **unrepresentative sample**, a genuine problem in machine learning. Player-added provisional labels can still be wrong. Other galaxy seeds, scan subsets and K/weight combinations may have different outcomes.

### Important: launch the WEB game, not the old Streamlit page

```powershell
git fetch origin
git switch --track origin/feat/playable-v0-7
python -m pip install -r requirements.txt -r requirements-web.txt
python -m uvicorn webapp.server:app --reload
```

Open **http://127.0.0.1:8000**. The older `streamlit run app.py` page at port **8501** is a different, archived interface and **does not contain the new navigation tabs**.

If the browser appears to show an old interface, use **Ctrl + Shift + R**; check for the **V0.7** badge and visit **http://127.0.0.1:8000/api/health** to confirm the server version. Stop and restart your old server if its version is outdated.

### Testing
GitHub Actions runs the Python API tests, a JavaScript syntax check, and a **real headless Chromium browser test** that launches the mission, switches tabs, verifies the version badge, scans all six reports, and checks the accuracy/precision improvement.


## V0.6 — Earn better AI predictions

**Branch:** `feat/playable-v0-6` (based on V0.5; no changes to the previous game branches).

### Why the AI now starts weak

The default local mission (seed 12) deliberately has *incomplete, biased training evidence*: most starter surveys concern ore-rich areas, while optional survey reports cover the underrepresented empty regions. This is a real K-nearest-neighbors algorithm, not an artificially rigged success/failure rate.

Using K=3 and Balanced sensors, on **20 held-out validation planets**:
- First model with 8 starter examples: **55% accuracy**
- After scanning all 6 reserve examples, 14 verified training examples: **85% accuracy**

Results for other seeds, K settings, player-provided provisional labels or partial scans can differ. Adding a single label can help, hurt or have no effect.

### Three navigation tabs

- **Explore Galaxy:** large star map, planet selection, evidence with genuine nearest neighbors and mining.
- **Train AI:** K, sensor weighting, labeled samples, scanning, Data Science Lab, and a training-history scorecard.
- **Missions & Results:** achievements, evidence-based post-mine diagnostics and permanent expedition log.

The prominent tutorial is optional and may be closed with X at any time, then reopened. In tutorial mode it switches to the relevant tab as each step progresses. Model A/B comparison and Research XP remain available.

Run: `python -m pip install -r requirements.txt -r requirements-web.txt` then `python -m uvicorn webapp.server:app --reload`.


## V0.5 — Refined tutorial and evidence-first right panel

This branch is forked from **feat/playable-v0-4**. The V0.4 branch is retained for comparison.

- The bright guided tutorial now has its own **X close button**, alongside Skip, Next Hint and the header's **Guided Tutorial** button for replay.
- The right sidebar follows one decision path: **Selected target (Heat/Spectrum) → KNN Evidence → Your Prediction → Mine**.
- **KNN Evidence** now shows the actual nearest training planets' **Heat, Spectrum, weighted distance, and stored ORE/EMPTY labels** in a compact table, including **DRAFT** warnings for unverified manual labels.
- The AI majority result (e.g. **2 ORE / 1 EMPTY**) is part of the KNN Evidence panel. Duplicate vote cards, separate nearest-neighbor buttons and the always-visible teaching box have been removed.
- The previous voting animation is still available using the small **replay** control; the sensor feature-space plot is an expandable part of the same evidence panel.
- Your own guess remains a separate conscious decision after reviewing the evidence; mining stays disabled until an answer is chosen.

These numbers are fictional planet features; player annotation remains provisional until verified by scanning. KNN uses weighted Euclidean sensor distances, not the decorative positions in the galaxy map.


## V0.4–V0.5 Learning Prototype (separate branch)

This experimental branch, `feat/playable-v0-4`, starts from the stable V0.3 `feat/playable-v0-1` commit. The older branch remains untouched for an A/B comparison. This PR targets the V0.3 branch, not `main`.

### New features

1. **Interactive cadet tutorial** — a guided on-screen walkthrough for training, choosing a target, seeing KNN votes, collecting labels, mining and comparing experiments; can be skipped or restarted.
2. **Sequential KNN vote reveal** — displays each actual nearest neighbor's identity, confirmed or provisional training label, and weighted sensor distance before showing the majority. The vote can be replayed on demand.
3. **Manual training-data annotation** — choose a reserve report and label it ORE or EMPTY. It enters the model as a clearly marked *provisional label*. You may update it. A 5-credit scan independently verifies the label, fixes errors and rewards a correct labeling hypothesis with 10 Research XP. No mining truth is disclosed.
4. **Frozen Model A vs Model B** — train, save Model A, change K / sensor focus / labels or scan, retrain Model B. Compare real held-out accuracy and each mining planet whose prediction changed. A prediction change is not automatically an improvement.
5. **Cadet Achievement Board** — seven server-derived objectives: first training, inspect three planets, annotate a report, correct a bad label, make a real model comparison, find three ore deposits, and correctly disagree with the AI. Achievements do not change ore labels or create free credits.
6. **Post-Mine Scientific Debrief** — review confirmed prediction errors, previous KNN voters, and suggested experiments. These hints do not reveal unmined labels.

### First playtest

- Launch Expedition (the tutorial activates automatically).
- Train with K=3, inspect a planet, click through each nearest neighbor's vote, and choose your own mining prediction.
- Label an optional training report, scan it to verify if desired, then retrain.
- Save the model as A, change K to 7 and retrain. Inspect the prediction-change list and validation accuracy difference.
- Replay the same seed with another strategy.

**Scientific honesty:** Unverified labels are labeled provisional in both UI and model evidence. They are the player's guesses, not the true mining answers. A model is only compared after training; no hardcoded improvement is awarded.

### How to run both versions

```powershell
git fetch origin
git switch --track origin/feat/playable-v0-4
python -m pip install -r requirements.txt -r requirements-web.txt
python -m uvicorn webapp.server:app --reload
```

If the branch already exists locally, use `git switch feat/playable-v0-4` and `git pull`.

To compare with the previous version, stop the server, run `git switch feat/playable-v0-1`, and restart the same command. Stop the server before switching branches so auto-reload does not mix application versions.


**Mission 01 — The Hidden Ore Galaxy**: learn machine learning by training a real K-nearest-neighbors (KNN) classifier and making mining decisions under limited resources.

## V0.3 — Understand the vote, play your own strategy

The V0.3 upgrade responds to player feedback:

1. **Inspect a planet** to see the *exact* surveyed planets participating in the KNN majority vote, their confirmed ore/empty labels, weighted sensor distances and a feature-space diagram connecting those examples to the target. The connections are **not physical star-to-star distances**.
2. **Choose K** and a **sensor focus**: Balanced, Heat ×2, or Spectrum ×2. These settings genuinely alter the Python KNN distance metric and can change votes. Train again to apply changes. The comparative validation results are genuine held-out accuracy scores.
3. **Strategic scouting:** when inspecting a planet, use the suggested unscanned training example that has the most similar sensors. Scanning costs 5 credits, reveals its confirmed label, and requires retraining; it does not reveal the mining candidate's hidden label.
4. **Human versus AI:** choose **I say ORE** or **I say EMPTY** before mining. Correct personal predictions award **20 Research XP**, a separate score from mining credits. The AI and player can disagree.
5. **Experiment:** replay the same galaxy with different K, sensor focus and scouting choices. True mineral labels stay fixed; no algorithm is guaranteed to be right.

The voted classification is not a calibrated probability: for example 2/3 ORE votes predicts ORE but does not mean 66.7% probability.

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
