# Space Miner AI

**Mission 01 — The Hidden Ore Galaxy**: a strategy-learning game powered by a real K-nearest-neighbors (KNN) classifier.

## Quick start

Requires Python 3.10+.

```bash
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# macOS/Linux: source .venv/bin/activate
python -m pip install -r requirements.txt
streamlit run app.py
```

Then open the local URL displayed by Streamlit (typically http://localhost:8501).

## How to play

1. Start with 100 credits and 8 known training planets.
2. Choose K = 1, 3, 5, or 7, and inspect the AI's predictions on mining candidates.
3. Optionally scan up to 6 extra training-sector planets for 5 credits each.
4. Mine up to 5 candidate planets for 10 credits each; successful mining returns 25 credits.
5. See outcomes, try new K values, and replay a seeded galaxy.

The galaxy is fictional. KNN calculates real Euclidean distances and majority votes. Validation accuracy is computed using 20 separate held-out planets. Mining candidate labels are never used for training or validation before mining.

## Tests

```bash
python -m pytest -q
```

## Repository layout

- `app.py` — interactive Streamlit game.
- `space_miner/core.py` — deterministic galaxy generator, KNN, evaluation and mining rules.
- `tests/test_core.py` — tests for repeatability, KNN accuracy, cheating prevention, and mining restrictions.

## Learning goals

Python functions and lists; mathematical distances; sorting; features and labels; KNN classification; held-out validation; checking model performance against a simple baseline.

## Next steps

Playtest the first three minutes with Moses. Improve the game based on feedback, then introduce Python Builder Mode exercises. The UI and game implementation are AI-assisted; Moses's learning progress must be assessed separately through independent Python challenges.
