# ✦ SPACE MINER AI

## V0.4–V0.5 Learning Prototype (separate branch)

This experimental branch, `feat/playable-v0-4`, starts from the stable V0.3 `feat/playable-v0-1` commit. The older branch remains untouched for an A/B comparison. This PR targets the V0.3 branch, not `main`.

### New features

1. **Interactive cadet tutorial** — a guided on-screen walkthrough for training, choosing a target, seeing KNN votes, collecting labels, mining and comparing experiments; can be skipped or restarted.
2. **Sequential KNN vote reveal** — displays each actual nearest neighbor's identity, confirmed or provisional training label, and weighted sensor distance before showing the majority. The vote can be replayed on demand.
3. **Manual training-data annotation** — choose a reserve report and label it ORE or EMPTY. It enters the model as a clearly marked *provisional label*. You may update it. A 5-credit scan independently verifies the label, fixes errors and rewards a correct labeling hypothesis with 10 Research XP. No mining truth is disclosed.
4. **Frozen Model A vs Model B** — train, save Model A, change K / sensor focus / labels or scan, retrain Model B. Compare real held-out accuracy and each mining planet whose prediction changed. A prediction change is not automatically an improvement.

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
