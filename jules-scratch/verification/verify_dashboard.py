from playwright.sync_api import Page, expect

def test_dashboard_and_calendar(page: Page):
    # 1. Arrange: Go to the login page.
    page.goto("http://localhost:3000/login")

    # 2. Act: Log in.
    page.get_by_label("Username").fill("testuser")
    page.get_by_label("Password").fill("password")
    page.get_by_role("button", name="Login").click()

    # 3. Assert: Confirm the navigation to the dashboard.
    expect(page).to_have_url("http://localhost:3000/")

    # 4. Screenshot: Capture the dashboard for visual verification.
    page.screenshot(path="jules-scratch/verification/dashboard.png")

    # 5. Act: Click on a calendar slot to open the modal.
    page.locator(".rbc-day-slot").first.click()

    # 6. Assert: Confirm the modal is open.
    expect(page.get_by_role("heading", name="Add Appointment")).to_be_visible()

    # 7. Screenshot: Capture the modal for visual verification.
    page.screenshot(path="jules-scratch/verification/modal.png")
