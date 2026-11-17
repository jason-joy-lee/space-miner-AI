"""Real Chromium regression for V0.7 tabs, version and training outcomes.

Optional for local pytest: install playwright and its Chromium browser to run.
GitHub Actions installs both, so browser coverage is required there.
"""
import contextlib
import socket
import subprocess
import sys
import time
from pathlib import Path
from urllib.request import urlopen

import pytest

pytest.importorskip("playwright.sync_api")
from playwright.sync_api import sync_playwright, expect

ROOT=Path(__file__).resolve().parents[1]


@pytest.fixture(scope="module")
def game_url():
    with socket.socket() as sock:
        sock.bind(("127.0.0.1",0))
        port=sock.getsockname()[1]
    server=subprocess.Popen(
        [sys.executable,"-m","uvicorn","webapp.server:app",
         "--host","127.0.0.1","--port",str(port)],
        cwd=ROOT,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL,
    )
    root=f"http://127.0.0.1:{port}"
    try:
        for _ in range(100):
            if server.poll() is not None:
                raise RuntimeError("Game server failed to start")
            try:
                with urlopen(root+"/api/health",timeout=.4) as response:
                    if response.status==200:
                        break
            except Exception:
                time.sleep(.1)
        else:
            raise RuntimeError("Game server did not respond")
        yield root
    finally:
        server.terminate()
        with contextlib.suppress(subprocess.TimeoutExpired):
            server.wait(timeout=5)
        if server.poll() is None:
            server.kill()
            server.wait(timeout=5)


def test_visible_top_tabs_and_teachable_accuracy(game_url):
    errors=[]
    with sync_playwright() as pw:
        browser=pw.chromium.launch(headless=True,args=["--no-sandbox"])
        try:
            page=browser.new_page(viewport={"width":1440,"height":900})
            page.on("pageerror",lambda error:errors.append(str(error)))
            page.goto(game_url,wait_until="networkidle")
            expect(page.locator(".version-flag")).to_have_text("V0.7")
            expect(page.locator(".startup-version")).to_contain_text("V0.7")
            expect(page.locator(".game-tabs")).to_be_visible()
            page.locator("#launch").click()
            # Guided tutorial opens the Train tab automatically.
            expect(page.locator("#page-train")).to_be_visible()
            expect(page.locator("#train")).to_be_visible()
            page.get_by_role("tab",name="Explore Galaxy").click()
            expect(page.locator("#page-explore")).to_be_visible()
            expect(page.locator("#map")).to_be_visible()
            expect(page.locator("#page-train")).to_be_hidden()
            page.get_by_role("tab",name="Missions & Results").click()
            expect(page.locator("#page-missions")).to_be_visible()
            expect(page.locator(".challenge-board")).to_be_visible()
            page.get_by_role("tab",name="Train AI").click()
            expect(page.locator("#train")).to_be_visible()
            page.locator("#train").click()
            expect(page.locator("#evaluation")).to_contain_text("35%")
            expect(page.locator("#training-journey")).to_contain_text("35%")
            # Verified surveys replace a biased training set with broader data.
            for _ in range(6):
                page.locator("#scan").click()
                expect(page.locator("#reveal")).to_be_visible()
                page.locator("#continue").click()
            page.locator("#train").click()
            expect(page.locator("#evaluation")).to_contain_text("85%")
            expect(page.locator("#evaluation")).to_contain_text("75%")
            expect(page.locator("#training-journey")).to_contain_text("50 points")
            page.get_by_role("tab",name="Explore Galaxy").click()
            expect(page.locator("#map")).to_be_visible()
            assert not errors,"JavaScript runtime errors: "+"; ".join(errors)
        finally:
            browser.close()
