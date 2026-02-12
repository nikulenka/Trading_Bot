
from playwright.sync_api import sync_playwright
import time

def run():
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page()
        page.goto("http://localhost:3000")
        time.sleep(5) # Wait for hydration
        page.screenshot(path="dashboard_verification.png", full_page=True)
        browser.close()

if __name__ == "__main__":
    run()
