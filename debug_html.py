"""Temporary diagnostic: saves raw HTML from SIGRH attendance page."""
import os
from pathlib import Path
from dotenv import load_dotenv
from playwright.sync_api import sync_playwright

load_dotenv()
username = os.environ["SIGRH_USERNAME"]
password = os.environ["SIGRH_PASSWORD"]

LOGIN_URL = "https://sigrh.ifes.edu.br/sigrh/login.jsf"
ATTENDANCE_URL = "https://sigrh.ifes.edu.br/sigrh/frequencia/espelho.jsf"

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False, slow_mo=800)
    page = browser.new_page()

    page.goto(LOGIN_URL)
    page.wait_for_load_state("networkidle")

    for sel in ["input[name='username']", "input[name='login']", "#username"]:
        if page.locator(sel).count():
            page.locator(sel).first.fill(username)
            break
    for sel in ["input[type='password']", "input[name='password']", "#password"]:
        if page.locator(sel).count():
            page.locator(sel).first.fill(password)
            break
    for sel in ["input[type='submit']", "button[type='submit']", "button:has-text('Entrar')"]:
        if page.locator(sel).count():
            page.locator(sel).first.click()
            break

    page.wait_for_load_state("networkidle")
    print(f"After login URL: {page.url}")

    page.goto(ATTENDANCE_URL)
    page.wait_for_load_state("networkidle")
    print(f"Attendance URL: {page.url}")
    print(f"Page title: {page.title()}")

    html = page.content()
    out = Path("data/debug_espelho.html")
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"HTML saved to {out} ({len(html)} bytes)")
    print("First 2000 chars of HTML:")
    print(html[:2000])

    browser.close()
