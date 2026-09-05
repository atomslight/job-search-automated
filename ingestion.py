from pathlib import Path
import pandas as pd
from pypdf import PdfReader


BASE_DIR = Path(__file__).resolve().parent

RESUME_FILE = BASE_DIR / "Agentic Ai Engineer.pdf"

# ============================================================
# CLEAN VALUE
# ============================================================

def clean_value(value):

    if pd.isna(value):
        return ""

    value = str(value)

    value = value.replace("\n", " ")
    value = value.replace("\r", " ")

    return " ".join(value.split())


# ============================================================
# LOAD CSV
# ============================================================

def load_jobs(csv_file):

    csv_file = Path(csv_file)

    if not csv_file.exists():
        raise FileNotFoundError(
            f"CSV not found: {csv_file}"
        )

    print(f"Using CSV: {csv_file}")

    return pd.read_csv(csv_file)


# ============================================================
# LOAD RESUME
# ============================================================

def load_resume(pdf_file=RESUME_FILE):

    reader = PdfReader(pdf_file)

    pages = []

    for page in reader.pages:

        text = page.extract_text()

        if text:
            pages.append(text)

    return "\n".join(pages).strip()


# ============================================================
# GET COMPLETE RECORDS
# ============================================================

def get_jobs(df):

    for index, row in df.iterrows():

        job_record = {
            column: clean_value(row[column])
            for column in df.columns
        }

        job_record["_row_index"] = index

        yield index, job_record
