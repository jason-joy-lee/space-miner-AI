"""Regression guards for the V0.5 evidence-first interface."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HTML = (ROOT/"webapp/static/index.html").read_text(encoding="utf-8")
JS = (ROOT/"webapp/static/game.js").read_text(encoding="utf-8")
CSS = (ROOT/"webapp/static/styles.css").read_text(encoding="utf-8")


def test_tutorial_can_be_closed_and_restarted():
    assert 'id="tutorial-close"' in HTML
    assert 'id="tutorial-skip"' in HTML
    assert 'id="tutorial-start"' in HTML
    assert "$('tutorial-close').onclick=closeTutorial" in JS
    assert "$('tutorial-skip').onclick=closeTutorial" in JS
    assert "$('tutorial-start').onclick=startTutorial" in JS
    assert "function closeTutorial(){tutorialStep=-1;renderTutorial()}" in JS
    assert ".tutorial-panel .tutorial-close" in CSS


def test_evidence_appears_before_decision_with_real_features():
    sidebar = HTML.split('<aside class="panel intel"',1)[1].split("</aside>",1)[0]
    assert sidebar.index('id="details"') < sidebar.index('id="voter-evidence"')
    assert sidebar.index('id="voter-evidence"') < sidebar.index('id="decision"')
    assert "function renderVoterEvidence()" in JS
    for title in ("HEAT", "SPEC.", "DIST.", "LABEL", "DRAFT"):
        assert title in JS
    assert "near.map(row)" in JS
    assert "n.heat" in JS and "n.spectrum" in JS and "n.distance" in JS
    assert "function renderDecision()" in JS


def test_duplicate_evidence_buttons_are_removed():
    assert 'SEE NEAREST NEIGHBORS' not in JS
    assert 'REPLAY KNN VOTES</button>' not in JS
    assert "id=\"replay-evidence\"" in JS
    assert "View sensor-space connections and distance math" in JS
    assert "Mining costs <b>10 Credits</b>" in JS
