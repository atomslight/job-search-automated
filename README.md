# 🕵️ Jobster
### Your automated, intelligent recruitment assistant.

## 📖 Overview
Jobster is an automated pipeline that scrapes job listings and intelligently matches them against your resume. By leveraging browser automation and Agentic AI, it eliminates the tedious manual search process, delivering a curated list of highly relevant opportunities tailored specifically to your background and skills.

## ✨ Features
*   **Automated Scraping**: Uses Playwright to drive Google Colab for scraping job boards without manual intervention.
*   **Intelligent Matching**: Employs CrewAI and local LLMs to evaluate job requirements against your actual resume.
*   **Strict Filtering**: Analyzes technical stack, experience level, and responsibilities to filter out irrelevant roles.
*   **Resume Parsing**: Automatically extracts text from your PDF resume for accurate comparisons.
*   **Keyword Management**: Tracks used search terms to ensure fresh job pulls on every run.
*   **Multi-Site Support**: Scrapes from Indeed, LinkedIn, ZipRecruiter, Google, Glassdoor, Bayt, Naukri, and BDJobs.

## 🛠 Tech Stack
*   **Python**: The core programming language powering the automation and data processing.
*   **Playwright**: Used for robust browser automation to interact with Google Colab.
*   **CrewAI**: Orchestrates AI agents to perform complex, multi-step reasoning tasks like job matching.
*   **Ollama**: Runs Large Language Models (LLMs) locally to ensure privacy and avoid API costs.
*   **Pandas & PyPDF**: Handles data manipulation for scraped CSVs and text extraction from PDF resumes.
*   **uv / pip**: Package managers used for handling dependencies.
*   **Node.js**: Underlying runtime for certain web tooling and automation features.

## 📋 Prerequisites
Before you start, ensure you have the following installed on your machine:
*   **Python**: v3.10 or higher.
*   **Node.js**: v18+ (Required for extended tooling and environment scripts).
*   **Git**: For cloning the repository.
*   **Ollama**: Installed and running locally (defaulting to `gemma4:31b-cloud` or your model of choice).
*   **Google Chrome**: Required for Playwright's persistent context.

## 🚀 Local Development (Step-by-Step)

### 1. Clone the Repository
```bash
git clone https://github.com/yourusername/jobster.git
cd jobster
```

### 2. Install Dependencies
You can install the core scraping library using `pip`:
```bash
pip install -U python-jobster
```
*(Optional)* If you are running the full automated pipeline with `uv`, use:
```bash
uv sync
uv run playwright install
```

### 3. Environment Setup
Create your environment configuration to point to your local Ollama instance and configure the AI model.
```bash
cp .env.example .env
```
Open the `.env` file and configure your API keys and endpoints. The project uses Ollama locally by default.
```env
OLLAMA_BASE_URL=http://localhost:11434/v1
OLLAMA_MODEL=gemma4:31b-cloud
```
Ensure your `keywords.txt` and `google-keywords.txt` files are populated with the job titles you want to search for, and place your resume as a PDF (e.g., `Agentic Ai Engineer.pdf`) in the project directory.

### 4. Run the Development Server
To start the automated job scraping and matching pipeline using the scripts:
```bash
uv run python automation.py
```
This will launch Chrome, navigate to the configured Colab notebook, extract jobs, and trigger the AI researcher to filter them against your resume.

---

## 💻 Usage (Programmatic)
If you want to use the Jobster scraper in your own scripts:

```python
import csv
from jobster import scrape_jobs

jobs = scrape_jobs(
    site_name=["indeed", "linkedin", "zip_recruiter", "google"],
    search_term="software engineer",
    google_search_term="software engineer jobs near San Francisco, CA since yesterday",
    location="San Francisco, CA",
    results_wanted=20,
    hours_old=72,
    country_indeed='USA',
    # linkedin_fetch_description=True # gets more info such as description, direct job url (slower)
    # proxies=["208.195.175.46:65095", "208.195.175.45:65095", "localhost"],
)
print(f"Found {len(jobs)} jobs")
print(jobs.head())
jobs.to_csv("jobs.csv", quoting=csv.QUOTE_NONNUMERIC, escapechar="\\", index=False) # to_excel
```

## 📊 Output
| SITE | TITLE | COMPANY | CITY | STATE | JOB_TYPE | INTERVAL | MIN_AMOUNT | MAX_AMOUNT | JOB_URL | DESCRIPTION |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| indeed | Software Engineer | AMERICAN SYSTEMS | Arlington | VA | None | yearly | 200000 | 150000 | https://www.indeed.com/... | THIS POSITION COMES WITH A 10K SIGNING BONUS!... |
| indeed | Senior Software Engineer | TherapyNotes.com | Philadelphia | PA | fulltime | yearly | 135000 | 110000 | https://www.indeed.com/... | About Us TherapyNotes is the national leader i... |
| linkedin | Software Engineer - Early Career | Lockheed Martin | Sunnyvale | CA | fulltime | yearly | None | None | https://www.linkedin.com/... | Description:By bringing together people that u... |
| linkedin | Full-Stack Software Engineer | Rain | New York | NY | fulltime | yearly | None | None | https://www.linkedin.com/... | Rain’s mission is to create the fastest and ea... |
| zip_recruiter | Software Engineer - New Grad | ZipRecruiter | Santa Monica | CA | fulltime | yearly | 130000 | 150000 | https://www.ziprecruiter... | We offer a hybrid work environment. Most US-ba... |

## ⚙️ Parameters for `scrape_jobs()`
*   `site_name (list|str)`: linkedin, zip_recruiter, indeed, glassdoor, google, bayt, bdjobs (default is all)
*   `search_term (str)`: The main job title/keyword to search.
*   `google_search_term (str)`: Search term for Google jobs. This is the only param for filtering Google jobs.
*   `location (str)`: The city, state, or area to search in.
*   `distance (int)`: In miles, default 50.
*   `job_type (str)`: fulltime, parttime, internship, contract.
*   `proxies (list)`: In format `['user:pass@host:port', 'localhost']`. Each job board scraper will round robin through the proxies.
*   `is_remote (bool)`: Filter for remote roles.
*   `results_wanted (int)`: Number of job results to retrieve for each site specified in `site_name`.
*   `easy_apply (bool)`: Filters for jobs that are hosted on the job board site. (LinkedIn easy apply filter no longer works).
*   `user_agent (str)`: Override the default user agent which may be outdated.
*   `description_format (str)`: `markdown`, `html` (Format type of the job descriptions. Default is `markdown`.)
*   `offset (int)`: Starts the search from an offset (e.g. 25 will start the search from the 25th result).
*   `hours_old (int)`: Filters jobs by the number of hours since the job was posted (ZipRecruiter and Glassdoor round up to the next day).
*   `verbose (int) {0, 1, 2}`: Controls the verbosity of the runtime printouts (0 prints only errors, 1 is errors+warnings, 2 is all logs. Default is 2).
*   `linkedin_fetch_description (bool)`: Fetches full description and direct job url for LinkedIn (Increases requests by O(n)).
*   `linkedin_company_ids (list[int])`: Searches for LinkedIn jobs with specific company ids.
*   `country_indeed (str)`: Filters the country on Indeed & Glassdoor (see below for correct spelling).
*   `enforce_annual_salary (bool)`: Converts wages to annual salary.
*   `ca_cert (str)`: Path to CA Certificate file for proxies.

### Site Limitations
*   **Indeed**: Only one from this list can be used in a search: `hours_old`, `job_type & is_remote`, `easy_apply`.
*   **LinkedIn**: Only one from this list can be used in a search: `hours_old`, `easy_apply`.

## 🌍 Supported Countries for Job Searching
*   **LinkedIn**: Searches globally & uses only the `location` parameter.
*   **ZipRecruiter**: Searches for jobs in US/Canada & uses only the `location` parameter.
*   **Indeed / Glassdoor**: Supports most countries, but the `country_indeed` parameter is required. Use the `location` parameter to narrow down the location.
*   **Bayt**: Only uses the `search_term` parameter currently and searches internationally.

*You can specify the following countries when searching on Indeed (use the exact name, `*` indicates support for Glassdoor):*
Argentina, Australia*, Austria*, Bahrain, Belgium*, Brazil*, Canada*, Chile, China, Colombia, Costa Rica, Czech Republic, Denmark, Ecuador, Egypt, Finland, France*, Germany*, Greece, Hong Kong*, Hungary, India*, Indonesia, Ireland*, Israel, Italy*, Japan, Kuwait, Luxembourg, Malaysia, Mexico*, Morocco, Netherlands*, New Zealand*, Nigeria, Norway, Oman, Pakistan, Panama, Peru, Philippines, Poland, Portugal, Qatar, Romania, Saudi Arabia, Singapore*, South Africa, South Korea, Spain*, Sweden, Switzerland*, Taiwan, Thailand, Turkey, Ukraine, United Arab Emirates, UK*, USA*, Uruguay, Venezuela, Vietnam*

## 📝 Notes & Tips
*   **Indeed is the best scraper currently** with no rate limiting. All the job board endpoints are capped at around 1000 jobs on a given search.
*   **LinkedIn is the most restrictive** and usually rate limits around the 10th page with one IP. Proxies are a must basically.

## ❓ Frequently Asked Questions (FAQ)

**Q: Why is Indeed giving unrelated roles?**
A: Indeed searches the description too. Use `-` to remove words, and `""` for exact match.
*Example of a good Indeed query:*
`search_term='"engineering intern" software summer (java OR python OR c++) 2025 -tax -marketing'`
This searches the description/title and must include software, summer, 2025, one of the languages, engineering intern exactly, no tax, no marketing.

**Q: No results when using "google"?**
A: You have to use super specific syntax. Search for google jobs on your browser and then whatever pops up in the google jobs search box after applying some filters is what you need to copy & paste into the `google_search_term`.

**Q: Received a response code 429?**
A: This indicates that you have been blocked by the job board site for sending too many requests. All of the job board sites are aggressive with blocking. We recommend:
1. Wait some time between scrapes (site-dependent).
2. Try using the `proxies` param to change your IP address.

## 🏗 Schema
```text
JobPost
├── title
├── company
├── company_url
├── job_url
├── location
│   ├── country
│   ├── city
│   ├── state
├── is_remote
├── description
├── job_type: fulltime, parttime, internship, contract
├── job_function
│   ├── interval: yearly, monthly, weekly, daily, hourly
│   ├── min_amount
│   ├── max_amount
│   ├── currency
│   └── salary_source: direct_data, description (parsed from posting)
├── date_posted
└── emails

Linkedin specific
└── job_level

Linkedin & Indeed specific
└── company_industry

Indeed specific
├── company_country
├── company_addresses
├── company_employees_label
├── company_revenue_label
├── company_description
└── company_logo

Naukri specific
├── skills
├── experience_range
├── company_rating
├── company_reviews_count
├── vacancy_count
└── work_from_home_type
```

## 🧠 How It Works (Architecture)
1. **Scraping**: `automation.py` reads a new keyword from your text files and uses Playwright to drive a Google Colab notebook. It modifies the search terms and triggers the Colab cell to scrape job data.
2. **Downloading**: A CSV of jobs is generated by Colab and downloaded automatically.
3. **Ingestion**: `ingestion.py` extracts your work history and skills from your PDF resume and loads the downloaded CSV.
4. **AI Analysis**: `researcher.py` uses CrewAI and Ollama to evaluate each job row against your parsed resume. It acts as a strict recruiter, ensuring your experience, technical skills, and seniority match the role.
5. **Output**: Only the highly relevant jobs are saved into a new, timestamped CSV file for you to review.

## 📁 Folder Structure
```text
.
├── automation.py       # Drives browser automation for scraping jobs via Colab.
├── connect.py          # Utility script to maintain the Playwright Colab connection.
├── ingestion.py        # Logic for parsing PDF resumes and loading CSV data.
├── researcher.py       # CrewAI script that evaluates jobs against the resume.
├── main.py             # Entry point for basic testing.
├── pyproject.toml      # Project configuration and dependency list.
└── uv.lock             # Dependency lockfile.
```