"""V0.6: the novice AI must start flawed and improve through real data."""
from pathlib import Path

from fastapi.testclient import TestClient

from space_miner.novice import novice_galaxy
from space_miner.core import accuracy, knn
from webapp.server import app

client=TestClient(app)
ROOT=Path(__file__).resolve().parents[1]
HTML=(ROOT/"webapp/static/index.html").read_text(encoding="utf-8")
JS=(ROOT/"webapp/static/game.js").read_text(encoding="utf-8")


def test_default_challenge_has_real_errors_then_improves_with_data():
    g=novice_galaxy(12)
    assert {key:len(value) for key,value in g.items()}=={
        "starter":8,"reserve":6,"validation":20,"mining":12
    }
    weak=accuracy(g["starter"],g["validation"],3)
    stronger=accuracy(g["starter"]+g["reserve"],g["validation"],3)
    assert weak==.35
    assert stronger==.85
    assert stronger-weak>=.20
    assert g==novice_galaxy(12)
    # Training never reads a candidate's hidden target label.
    candidate=g["mining"][0]
    from space_miner.core import Planet
    swapped=Planet(candidate.id,candidate.thermal,candidate.spectral,not candidate.ore)
    assert knn(g["starter"],candidate,3)[0]==knn(g["starter"],swapped,3)[0]


def test_training_history_is_server_derived_without_target_labels():
    m=client.post("/api/missions",json={"seed":12}).json()
    root=f"/api/missions/{m['session_id']}"
    assert m["training_history"]==[]
    first=client.post(root+"/train",json={"k":3,"focus":"balanced"}).json()
    assert first["training_history"][0]["accuracy"]==.35
    assert "predictions" not in first["training_history"][0]
    assert first["training_history"][0]["changed_count"] is None
    after=first
    for planet in first["reserve"]:
        after=client.post(root+"/scan",json={"planet_id":planet["id"]}).json()
    assert after["trained"] is False
    final=client.post(root+"/train",json={"k":3,"focus":"balanced"}).json()
    history=final["training_history"]
    assert len(history)==2
    assert history[1]["training_count"]==14
    assert history[1]["accuracy"]==.85
    assert history[1]["accuracy_delta"]==.50
    assert history[1]["changed_count"]>=1
    assert history[0]["precision"]==.35
    assert history[1]["precision"]==.75
    assert history[1]["precision_delta"]==.40
    assert all("predictions" not in h for h in history)


def test_top_tabs_preserve_game_and_existing_learning_controls():
    assert HTML.index('data-page="explore"')<HTML.index('data-page="train"')<HTML.index('data-page="missions"')
    for element in ("page-explore","page-train","page-missions","explore-map",
                    "explore-intel","train-controls","train-lab","mission-tasks",
                    "training-journey"):
        assert 'id="'+element+'"' in HTML
    assert "function initializeTabs()" in JS
    assert "function setPage(name)" in JS
    assert "function renderTrainingJourney()" in JS
    assert "renderTrainingJourney();" in JS
    assert "appendChild(document.querySelector('.central'))" in JS
    assert "appendChild(document.querySelector('.intel'))" in JS
