from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch()
    page = browser.new_page()
    page.goto("http://localhost:3000/login")
    page.screenshot(path="jules-scratch/verification/login_page.png")
    page.get_by_label("Username").fill("testuser")
    page.get_by_label("Password").fill("password")
    page.get_by_role("button", name="Submit").click()
    page.wait_for_url("http://localhost:3000/")
    page.screenshot(path="jules-scratch/verification/dashboard_page.png")
    browser.close()

with sync_playwright() as playwright:
    run(playwright)
