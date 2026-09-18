"""Drive the Streamlit buddy UI and record a short live-model smoke walkthrough."""

from __future__ import annotations

import json
import re
import time
from pathlib import Path

from playwright.sync_api import Page, sync_playwright

URL = "http://127.0.0.1:8501"
OUT_DIR = Path(__file__).resolve().parent
SHOT_DIR = Path("/tmp/buddy-ui-shots")
VIDEO_DIR = Path("/tmp/buddy-ui-video")
NOTES = Path("/tmp/buddy-ui-notes.json")


def wait_idle(page: Page, timeout_ms: int = 20000) -> None:
    page.wait_for_timeout(250)
    try:
        page.wait_for_function(
            """() => {
              const t = document.body.innerText || '';
              return !t.includes('Running...') && !t.includes('Please wait');
            }""",
            timeout=timeout_ms,
        )
    except Exception:
        pass
    page.wait_for_timeout(400)


def body_text(page: Page) -> str:
    return page.inner_text("body")


def slider_value(page: Page) -> str:
    thumb = page.locator('[data-testid="stSliderThumbValue"]').first
    if thumb.count():
        return (thumb.inner_text() or "").strip()
    return ""


def set_weight_kg(page: Page, kg: float, height_cm: float = 174.0) -> None:
    """Move the linked what-if via BMI (Streamlit range thumbs drop keypresses)."""
    height_m = height_cm / 100.0
    bmi = round(kg / (height_m**2), 1)
    field = page.locator('[data-testid="stNumberInputField"]')
    field.scroll_into_view_if_needed()
    field.click()
    page.wait_for_timeout(200)
    field.press("Control+A")
    field.fill(f"{bmi:.1f}")
    field.press("Enter")
    wait_idle(page)


def main() -> None:
    SHOT_DIR.mkdir(parents=True, exist_ok=True)
    VIDEO_DIR.mkdir(parents=True, exist_ok=True)
    notes: dict = {"steps": []}

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={"width": 1440, "height": 920},
            record_video_dir=str(VIDEO_DIR),
            record_video_size={"width": 1440, "height": 920},
        )
        page = context.new_page()
        page.goto(URL, wait_until="domcontentloaded", timeout=60000)
        page.wait_for_selector("text=Hoi River", timeout=30000)
        wait_idle(page)
        page.wait_for_timeout(2200)

        text0 = body_text(page)
        notes["steps"].append(
            {
                "name": "home_river_live",
                "has_live_caption": "Live Kylie-modellen" in text0,
                "has_92": "92%" in text0,
                "has_91": "91%" in text0,
                "slider": slider_value(page),
                "river_selected": "Hoi River" in text0,
            }
        )
        page.screenshot(path=str(SHOT_DIR / "01_river_live_94kg.png"), full_page=True)

        # Ensure River + live toggle (already default)
        page.get_by_text("River", exact=True).first.click()
        wait_idle(page)

        set_weight_kg(page, 101.5)
        page.wait_for_timeout(2000)
        text1 = body_text(page)
        notes["steps"].append(
            {
                "name": "weight_up",
                "slider": slider_value(page),
                "has_93": "93%" in text1,
                "has_92": "92%" in text1,
                "snippet_risk": "93%" in text1 or "92%" in text1,
            }
        )
        page.screenshot(path=str(SHOT_DIR / "02_river_live_heavier.png"), full_page=True)

        # Groningen walk is secondary under live models
        page.locator("text=Beweging").first.scroll_into_view_if_needed()
        page.wait_for_timeout(400)
        opens = page.get_by_role("button", name=re.compile(r"^Open$"))
        if opens.count() == 0:
            page.get_by_role("button", name=re.compile(r"wandeling|voeding|Open", re.I)).first.click()
        else:
            opens.first.click()
        wait_idle(page)
        page.wait_for_timeout(1800)
        text2 = body_text(page)
        notes["steps"].append(
            {
                "name": "intervention_detail",
                "has_groningen": "groningen" in text2.lower() or "plantsoen" in text2.lower() or "martini" in text2.lower(),
                "title_bit": text2.split("\n")[:12],
            }
        )
        page.screenshot(path=str(SHOT_DIR / "03_intervention.png"), full_page=True)

        page.get_by_role("button", name=re.compile(r"Terug naar Boris")).click()
        wait_idle(page)
        page.wait_for_timeout(1600)
        text3 = body_text(page)
        notes["steps"].append(
            {
                "name": "back_home",
                "slider": slider_value(page),
                "reset_toward_45": "45" in slider_value(page) or "Hoi River" in text3 and "45.00" in text3,
                "text_has_45kg": "45.00" in text3 or "45,00" in text3,
            }
        )
        page.screenshot(path=str(SHOT_DIR / "04_back_home.png"), full_page=True)

        # Quirk is visible on return (slider ~45). Reset so chat is on a sane weight.
        reset = page.get_by_role("button", name="Reset")
        if reset.count():
            reset.click()
            wait_idle(page)
            page.wait_for_timeout(800)

        expander = page.locator('[data-testid="stExpander"]')
        expander.scroll_into_view_if_needed()
        expander.click()
        page.wait_for_timeout(400)
        page.locator('[data-testid="stTextInput"] input').fill("Should I take metformin?")
        page.get_by_role("button", name="Vraag").click()
        wait_idle(page)
        page.wait_for_timeout(1000)
        page.locator("text=geen zorgverlener").first.scroll_into_view_if_needed()
        page.wait_for_timeout(800)
        text4 = body_text(page)
        notes["steps"].append(
            {
                "name": "ask_metformin",
                "guardrail": "geen zorgverlener" in text4.lower() or "medicatie" in text4.lower(),
            }
        )
        page.screenshot(path=str(SHOT_DIR / "05_metformin.png"), full_page=True)

        page.locator('[data-testid="stTextInput"] input').fill("wandelen Groningen")
        page.get_by_role("button", name="Vraag").click()
        wait_idle(page)
        page.wait_for_timeout(1200)
        page.locator("text=Start with walks").first.scroll_into_view_if_needed()
        page.wait_for_timeout(1500)
        text5 = body_text(page)
        notes["steps"].append(
            {
                "name": "ask_wandelen",
                "coaching": "walk" in text5.lower() or "wandel" in text5.lower() or "movement" in text5.lower(),
                "still_guardrail_only": text5.lower().count("geen zorgverlener") >= 1 and "walk" not in text5.lower(),
            }
        )
        page.screenshot(path=str(SHOT_DIR / "06_wandelen.png"), full_page=True)
        page.wait_for_timeout(1500)

        video_path = Path(page.video.path()) if page.video else None
        context.close()
        browser.close()
        notes["playwright_video"] = str(video_path) if video_path else None
        NOTES.write_text(json.dumps(notes, indent=2), encoding="utf-8")
        print(json.dumps(notes, indent=2))
        if video_path:
            print("VIDEO", video_path)


if __name__ == "__main__":
    main()
