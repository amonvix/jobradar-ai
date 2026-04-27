# JobRadar AI

JobRadar AI is a modular Python CLI project that collects job postings from configurable job websites, matches postings against a CV, ranks them by relevance, deduplicates repeated jobs, and generates a Markdown report.

## Features

- Python 3.12+ compatible CLI (`main.py`)
- Config-driven sites and keywords
- CV-aware relevance scoring
- Duplicate removal by title/company/url
- SQLite persistence for raw and ranked jobs
- Markdown report generation (`reports/jobs_report.md`)
- Structured modules designed for easy migration to a FastAPI backend
- Logging and robust error handling

## Project Structure

```text
jobradar-ai/
├── main.py
├── jobradar/
│   ├── collectors/
│   ├── matcher/
│   ├── ranking/
│   ├── reports/
│   ├── storage/
│   ├── config.py
│   ├── logging_utils.py
│   ├── models.py
│   └── pipeline.py
├── config/
│   ├── sites.json
│   ├── keywords.json
│   └── cv.txt
├── data/
├── reports/
└── requirements.txt
```

## Setup

1. **Create virtual environment**

   ```bash
   python3.12 -m venv .venv
   source .venv/bin/activate
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Edit configs**
   - `config/sites.json`: add target job sites and CSS selector for job links.
   - `config/keywords.json`: add search and relevance keywords.
   - `config/cv.txt`: paste your latest CV text.

## Usage

Run with defaults:

```bash
python main.py
```

Run with explicit paths:

```bash
python main.py \
  --sites config/sites.json \
  --keywords config/keywords.json \
  --cv config/cv.txt \
  --db data/jobradar.sqlite \
  --report reports/jobs_report.md \
  --log-level INFO
```

## Output Artifacts

- **SQLite DB**: `data/jobradar.sqlite`
  - `raw_jobs` table stores every fetched candidate.
  - `ranked_jobs` table stores deduplicated scored jobs.
- **Markdown report**: `reports/jobs_report.md`

## Migration Path to FastAPI

The CLI orchestration is isolated in `jobradar/pipeline.py`. Core modules (`collectors`, `matcher`, `ranking`, `storage`, and `reports`) are decoupled and can be reused in API route handlers with minimal refactoring.

## Notes

- Some websites may block scraping or require JavaScript rendering; this project intentionally starts with `requests + BeautifulSoup` for simplicity.
- Respect each website's terms of service and robots.txt before scraping.
