from playwright.sync_api import sync_playwright

def run(playwright):
    browser = playwright.chromium.launch()
    page = browser.new_page()

    # Register a new user
    response = page.request.post("http://127.0.0.1:5000/api/register", data={
        "username": "testuser",
        "password": "password"
    })

    browser.close()

with sync_playwright() as playwright:
    run(playwright)
