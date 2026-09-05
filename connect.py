from playwright.sync_api import sync_playwright

PROFILE_DIR = r"E:\Jobster\chrome-profile"
NOTEBOOK_URL = "https://colab.research.google.com/drive/1Drf1FEG4MmorwmKSkB4RjGJKASWnTtff"

with sync_playwright() as p:

    context = p.chromium.launch_persistent_context(
        user_data_dir=PROFILE_DIR,
        headless=False,
        channel="chrome"
    )

    page = context.pages[0] if context.pages else context.new_page()

    page.goto(NOTEBOOK_URL)

    page.wait_for_timeout(5000)

    print("URL:", page.url)
    print("TITLE:", page.title())

    input("Press Enter to close...")
    
    context.close()