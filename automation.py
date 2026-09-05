from pathlib import Path
from playwright.sync_api import Playwright, sync_playwright
import time
import sys

import subprocess
import sys
# ==========================================
# SETTINGS
# ==========================================

PROFILE_DIR = r"E:\JobSpy\chrome-profile"

NOTEBOOK_URL = (
    "https://colab.research.google.com/drive/"
    "1Drf1FEG4MmorwmKSkB4RjGJKASWnTtff"
)

DOWNLOAD_DIR = Path(r"E:\JobSpy\jobs_extracted")

KEYWORDS_FILE = Path(r"E:\JobSpy\keywords.txt")
GOOGLE_KEYWORDS_FILE = Path(r"E:\JobSpy\google-keywords.txt")

USED_KEYWORDS_FILE = Path(r"E:\JobSpy\used_keywords.txt")
USED_GOOGLE_KEYWORDS_FILE = Path(
    r"E:\JobSpy\used_google-keywords.txt"
)


# ==========================================
# GET NEXT UNUSED KEYWORD
# ==========================================

def get_next_keyword(source_file, used_file):

    if not source_file.exists():
        raise Exception(
            f"File not found: {source_file}"
        )

    used = set()

    if used_file.exists():
        used = {
            line.strip()
            for line in used_file.read_text(
                encoding="utf-8"
            ).splitlines()
            if line.strip()
        }

    for line in source_file.read_text(
        encoding="utf-8"
    ).splitlines():

        keyword = line.strip()

        if keyword and keyword not in used:
            return keyword

    raise Exception(
        f"No unused keywords remaining in "
        f"{source_file.name}"
    )


# ==========================================
# MARK KEYWORD AS USED
# ==========================================

def mark_used(keyword, source_file, used_file):

    with used_file.open(
        "a",
        encoding="utf-8"
    ) as f:
        f.write(keyword + "\n")

    lines = source_file.read_text(
        encoding="utf-8"
    ).splitlines()

    remaining = []
    removed = False

    for line in lines:

        if not removed and line.strip() == keyword:
            removed = True
            continue

        remaining.append(line)

    source_file.write_text(
        "\n".join(remaining)
        + ("\n" if remaining else ""),
        encoding="utf-8"
    )


def find_code_line(cell, text_to_find):

    editor = cell.get_by_role(
        "textbox",
        name="Editor content"
    )

    editor.wait_for(
        state="visible",
        timeout=15000
    )

    scroll_area = cell.locator(
        ".monaco-scrollable-element.editor-scrollable"
    ).first

    scroll_area.wait_for(
        state="visible",
        timeout=10000
    )

    # Start from top of the Monaco editor
    scroll_area.evaluate(
        "(el) => el.scrollTop = 0"
    )

    for _ in range(20):

        line = cell.locator(
            ".view-line",
            has_text=text_to_find
        ).first

        if line.count() and line.is_visible():
            return line, editor

        scroll_area.evaluate(
            "(el) => el.scrollTop += el.clientHeight"
        )

        cell.page.wait_for_timeout(150)

    raise Exception(
        f"Could not find '{text_to_find}' inside Cell 4."
    )


def modify_line(cell, text_to_find, new_line):

    line, editor = find_code_line(
        cell,
        text_to_find
    )

    line.click()

    editor.press("Home")
    editor.press("Shift+End")
    editor.type(new_line)

# ==========================================
# MAIN
# ==========================================

def run(playwright: Playwright):

    DOWNLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    context = None

    try:

        # ======================================
        # GET KEYWORDS
        # ======================================

        search_keyword = get_next_keyword(
            KEYWORDS_FILE,
            USED_KEYWORDS_FILE
        )

        google_keyword = get_next_keyword(
            GOOGLE_KEYWORDS_FILE,
            USED_GOOGLE_KEYWORDS_FILE
        )

        print("Search keyword:")
        print(search_keyword)

        print("Google keyword:")
        print(google_keyword)


        # ======================================
        # PERSISTENT CHROME
        # ======================================

        context = playwright.chromium.launch_persistent_context(
            user_data_dir=PROFILE_DIR,
            headless=False,
            channel="chrome",
            accept_downloads=True
        )

        page = (
            context.pages[0]
            if context.pages
            else context.new_page()
        )


        # ======================================
        # OPEN COLAB
        # ======================================

        print("Opening Colab...")

        page.goto(
            NOTEBOOK_URL,
            wait_until="domcontentloaded"
        )

        page.wait_for_timeout(5000)

        print("Colab loaded:")
        print(page.title())


        # ======================================
        # CELL 4 ONLY
        # ======================================

        print("Opening Cell 4...")

        page.locator(
            ".view-lines",
            has_text="pip install -U python-jobspy"
        ).click()

        cell4 = page.get_by_role(
            "region",
            name="Cell 0: Code cell: "
        )

        page.get_by_role(
            "region",
            name="Cell 0: Code cell: "
        ).press("ArrowDown")

        # Cell 4 exact DOM id
        cell4 = page.locator(
            "#cell-67GS5-E-e6O3"
        )

        cell4.wait_for(
            state="visible",
            timeout=20000
        )


        # ======================================
        # MODIFY search_term
        # ======================================

        print("Updating search_term...")

        modify_line(
            cell4,
            "search_term=",
            f'    search_term="{search_keyword}",'
        )


        # ======================================
        # MODIFY google_search_term
        # ======================================

        print("Updating google_search_term...")

        modify_line(
            cell4,
            "google_search_term=",
            f'    google_search_term="{google_keyword}",'
        )

        print()
        print(
            "Only the two keyword lines were modified."
        )


        # ======================================
        # RUN CELL 4 ONCE
        # ======================================

        print("Running Cell 4...")

        with page.expect_download(
            timeout=300000
        ) as download_info:

            cell4.get_by_role(
                "button",
                name="Run cell"
            ).click()


        # ======================================
        # DOWNLOAD
        # ======================================

        download = download_info.value

        print(
            "Colab generated:",
            download.suggested_filename
        )

        output_file = (
            DOWNLOAD_DIR
            / download.suggested_filename
        )
        
        download.save_as(
            str(output_file)
        )
        

        # ======================================
        # VERIFY
        # ======================================

        if not output_file.exists():
            raise Exception(
                "Download completed but file was not found."
            )

        if output_file.stat().st_size == 0:
            raise Exception(
                "Downloaded CSV is empty."
            )

        
        # ======================================
        # MARK KEYWORDS USED
        # ONLY AFTER SUCCESS
        # ======================================

        mark_used(
            search_keyword,
            KEYWORDS_FILE,
            USED_KEYWORDS_FILE
        )

        mark_used(
            google_keyword,
            GOOGLE_KEYWORDS_FILE,
            USED_GOOGLE_KEYWORDS_FILE
        )
        RESEARCHER_DIR = r"E:\CrewAi\Lead Apify"
        RESEARCHER_SCRIPT = r"E:\CrewAi\Lead Apify\Agents\researcher.py"

        subprocess.run(
            [
                "uv",
                "run",
                "python",
                RESEARCHER_SCRIPT,
                str(output_file)
            ],
            cwd=RESEARCHER_DIR,
            check=True
        )
        # ======================================
        # SUCCESS
        # ======================================

        print()
        print("====================================")
        print("JOBSPY COMPLETED SUCCESSFULLY")
        print("====================================")
        print("File:")
        print(output_file)
        print()
        print("Search:")
        print(search_keyword)
        print()
        print("Google:")
        print(google_keyword)
        print("====================================")


    except Exception as e:

        print()
        print("====================================")
        print("JOBSPY AUTOMATION FAILED")
        print("====================================")
        print(
            "Error type:",
            type(e).__name__
        )
        print(
            "Error:",
            str(e)
        )
        print("====================================")

        # Do not mark keywords as used.
        raise


    finally:

        if context:

            try:
                context.close()
            except Exception:
                pass



# ==========================================
# START
# ==========================================

with sync_playwright() as playwright:
    run(playwright)
