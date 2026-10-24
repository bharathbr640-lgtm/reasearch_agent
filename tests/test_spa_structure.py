"""Tier 1 and Tier 4 DOM & UI Structure Verification Tests for the SPA Layout."""

import os
from pathlib import Path
from bs4 import BeautifulSoup
import pytest
from starlette.testclient import TestClient

try:
    from playwright.sync_api import sync_playwright
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False


# ══════════════════════════════════════════════════════════════════════
# TIER 1: Structural SPA Contract & Container Presence
# ══════════════════════════════════════════════════════════════════════

def test_tier1_spa_four_view_containers_present_in_prototype(prototype_html_path: Path):
    """The authoritative SPA prototype must define all 4 required view containers."""
    assert prototype_html_path.exists(), f"Prototype file not found at {prototype_html_path}"
    with open(prototype_html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    required_views = [
        "view-dashboard",
        "view-start",
        "view-active",
        "view-report",
    ]
    for view_id in required_views:
        el = soup.find(id=view_id)
        assert el is not None, f"Required SPA view container '#{view_id}' missing in prototype"


def test_tier1_essential_spa_components_present(prototype_html_path: Path):
    """Authoritative prototype must include sidebar, toast, input, and telemetry elements."""
    with open(prototype_html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    required_elements = {
        "toast-notification": "Floating toast notification container",
        "toast-message": "Toast message text span",
        "btn-sidebar-new": "Sidebar 'New Research' primary CTA button",
        "dashboard-input": "Dashboard quick problem textarea",
        "dash-char-count": "Dashboard character counter display",
        "start-problem-textarea": "Start view research intake textarea",
        "start-char-count": "Start view character counter display",
        "active-progress-bar": "Active session visual progress bar",
        "telemetry-log": "Active session telemetry log console",
        "rep-sec-1": "Report Section 01: Executive Summary",
        "rep-sec-4": "Report Section 04: Comparative Evaluation Matrix",
        "rep-sec-6": "Report Section 06: Recommended Next Steps",
    }
    for el_id, desc in required_elements.items():
        assert soup.find(id=el_id) is not None, f"Required UI element '{el_id}' ({desc}) missing"


def test_tier1_dashboard_workflow_and_metrics(prototype_html_path: Path):
    """Dashboard view must include workflow preview cards and metrics snapshot."""
    with open(prototype_html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    dash = soup.find(id="view-dashboard")
    assert dash is not None

    # Check for suggested domain tags (NLP, Vision, RL, Systems)
    text_content = dash.get_text()
    assert "Natural Language Processing" in text_content or "NLP" in text_content
    assert "Computer Vision" in text_content or "Vision" in text_content

    # Check for pipeline overview stage labels
    assert "Orchestrator" in text_content
    assert "Project Finder" in text_content
    assert "Paper Finder" in text_content
    assert "Evaluator" in text_content


def test_tier1_start_view_presets_and_intake(prototype_html_path: Path):
    """Start view must include recommended benchmark cards and problem input."""
    with open(prototype_html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    start_view = soup.find(id="view-start")
    assert start_view is not None

    # Verify benchmark preset references exist
    text_content = start_view.get_text()
    assert "Crop Yield" in text_content or "Clinical LLM" in text_content or "Drone" in text_content


def test_tier1_active_view_agent_cards_and_telemetry(prototype_html_path: Path):
    """Active view must contain agent status telemetry and progress tracking."""
    with open(prototype_html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    active_view = soup.find(id="view-active")
    assert active_view is not None

    assert active_view.find(id="active-progress-bar") is not None
    assert active_view.find(id="telemetry-log") is not None


def test_tier1_report_view_sections(prototype_html_path: Path):
    """Report view must contain executive summary and evaluation data table."""
    with open(prototype_html_path, "r", encoding="utf-8") as f:
        soup = BeautifulSoup(f.read(), "html.parser")

    report_view = soup.find(id="view-report")
    assert report_view is not None

    assert report_view.find(id="rep-sec-1") is not None
    assert report_view.find(id="rep-sec-4") is not None
    assert report_view.find(id="rep-sec-6") is not None


def test_tier1_live_root_page_serves_html(sync_client: TestClient):
    """GET / serves valid HTML with DOCTYPE, head, and body tags."""
    response = sync_client.get("/")
    assert response.status_code == 200
    soup = BeautifulSoup(response.text, "html.parser")

    assert soup.find("html") is not None
    assert soup.find("head") is not None
    assert soup.find("body") is not None
    assert soup.find("title") is not None


def test_tier1_live_spa_view_containers_contract(sync_client: TestClient):
    """When M2 unified workspace is deployed to static/index.html, verify 4 view containers on live server."""
    response = sync_client.get("/")
    assert response.status_code == 200
    soup = BeautifulSoup(response.text, "html.parser")

    # If M2 unified workspace layout has been deployed to static/index.html
    dash = soup.find(id="view-dashboard")
    if dash is not None:
        for vid in ["view-dashboard", "view-start", "view-active", "view-report"]:
            assert soup.find(id=vid) is not None, f"Live SPA missing view container #{vid}"
    else:
        # Pre-M2 stage: initial template verified by test_tier1_live_root_page_serves_html
        pytest.skip("M2 SPA layout not yet deployed to static/index.html (current milestone is M1)")


# ══════════════════════════════════════════════════════════════════════
# TIER 4: Headless Playwright DOM Navigation & Zero Uncaught Exceptions
# ══════════════════════════════════════════════════════════════════════

@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="playwright is not installed")
def test_tier4_playwright_zero_uncaught_errors(prototype_html_path: Path):
    """Authoritative prototype must load in Chromium with zero uncaught JavaScript errors."""
    page_errors: list[str] = []

    file_url = f"file://{prototype_html_path.resolve()}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.on("pageerror", lambda err: page_errors.append(str(err)))

        page.goto(file_url)
        assert page.title() != ""
        browser.close()

    assert len(page_errors) == 0, f"Uncaught page errors detected: {page_errors}"


@pytest.mark.skipif(not PLAYWRIGHT_AVAILABLE, reason="playwright is not installed")
def test_tier4_playwright_view_switching_navigation(prototype_html_path: Path):
    """View switching mechanism transitions views cleanly without uncaught script exceptions."""
    page_errors: list[str] = []
    file_url = f"file://{prototype_html_path.resolve()}"

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.on("pageerror", lambda err: page_errors.append(str(err)))

        page.goto(file_url)

        # Click sidebar 'New Research' button -> triggers switchView('start')
        page.click("#btn-sidebar-new")
        assert page.locator("#view-start").is_visible(), "Expected #view-start to be visible after clicking #btn-sidebar-new"
        assert not page.locator("#view-dashboard").is_visible(), "Expected #view-dashboard to be hidden"

        # Switch to active view
        page.evaluate("switchView('active')")
        assert page.locator("#view-active").is_visible(), "Expected #view-active to be visible after switchView('active')"
        assert not page.locator("#view-start").is_visible(), "Expected #view-start to be hidden"

        # Switch to report view
        page.evaluate("switchView('report')")
        assert page.locator("#view-report").is_visible(), "Expected #view-report to be visible after switchView('report')"
        assert not page.locator("#view-active").is_visible(), "Expected #view-active to be hidden"

        # Switch back to dashboard view
        page.evaluate("switchView('dashboard')")
        assert page.locator("#view-dashboard").is_visible(), "Expected #view-dashboard to be visible after switchView('dashboard')"
        assert not page.locator("#view-report").is_visible(), "Expected #view-report to be hidden"

        browser.close()

    assert len(page_errors) == 0, f"Uncaught page errors during view switching: {page_errors}"
