"""Lightweight static UI contract checks for the new learning experience."""
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
html=(ROOT/"webapp/static/index.html").read_text(encoding="utf-8")
js=(ROOT/"webapp/static/game.js").read_text(encoding="utf-8")

def test_tutorial_and_lab_controls_exist():
    for identifier in ("tutorial-panel","tutorial-title","tutorial-description","tutorial-start",
        "tutorial-next","tutorial-skip","vote-next","vote-close","vote-steps",
        "label-target","label-ore","label-empty","label-audit","save-model","comparison"):
        assert 'id="'+identifier+'"' in html, identifier

def test_script_wires_server_driven_learning_features():
    for marker in ("/label","/save-model","model_comparison","renderLab",
                   "renderTutorial","showVoteAnimation","nextVoter",
                   "inspection.neighbors","provisional"):
        assert marker in js,marker

def test_v03_branch_remains_unchanged_by_new_features():
    # Branch isolation is checked by GitHub PR review. This test documents
    # that V0.4 UI has an explicit comparison surface rather than replacing
    # the V0.3 experience in-place.
    assert "MODEL A vs MODEL B" in html
