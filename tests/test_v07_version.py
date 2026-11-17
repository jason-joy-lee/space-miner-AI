"""Keep the user-visible release version consistent in every entry point."""
from pathlib import Path

from fastapi.testclient import TestClient
from webapp.server import app
from webapp.version import DISPLAY_VERSION, VERSION

ROOT=Path(__file__).resolve().parents[1]


def test_visible_version_matches_server_and_static_asset_urls():
    html=(ROOT/"webapp/static/index.html").read_text(encoding="utf-8")
    readme=(ROOT/"README.md").read_text(encoding="utf-8")
    assert DISPLAY_VERSION=="V0.7"
    assert VERSION=="0.7.0"
    assert app.version==VERSION
    assert TestClient(app).get("/api/health").json()["version"]==VERSION
    assert 'class="version-flag"' in html
    assert 'class="startup-version"' in html
    assert html.count(DISPLAY_VERSION)>=3
    assert "/static/game.js?v=0.7" in html
    assert "/static/styles.css?v=0.7" in html
    assert DISPLAY_VERSION in readme
