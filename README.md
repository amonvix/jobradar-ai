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
- Retry and timeout handling for more resilient collectors
- Debug options for HTML snapshot troubleshooting

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
   - `config/keywords.json`: configure `positive_keywords`, `negative_keywords`, and `target_role_groups`.
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

Debug run (save fetched HTML snapshots and enable verbose logs):

```bash
python main.py --debug --debug-html
```


## Matching & Ranking Behavior

- Positive keywords and CV token overlap increase scores.
- Target role-group hits (Incident Management, Production Support, Application Support, Cloud Operations, Technical Support) provide additional scoring boost.
- Negative keyword hits (`sales`, `director`, `marketing`, `business development`, `account executive`, `recruiter`, `hr`, `finance`, `legal`) are excluded from final ranking by default.

## Output Artifacts

- **SQLite DB**: `data/jobradar.sqlite`
  - `raw_jobs` table stores every fetched candidate.
  - `ranked_jobs` table stores deduplicated scored jobs.
- **Markdown report**: `reports/jobs_report.md`

## Migration Path to FastAPI

The CLI orchestration is isolated in `jobradar/pipeline.py`. Core modules (`collectors`, `matcher`, `ranking`, `storage`, and `reports`) are decoupled and can be reused in API route handlers with minimal refactoring.

## Notes

- Some websites may block scraping or require JavaScript rendering; this project intentionally starts with `requests + BeautifulSoup` for simplicity.
- The collector handles retries/timeouts and gracefully skips WeWorkRemotely 403 responses unless `--debug` is enabled.
- RemoteOK collection supports API-first fetching with HTML/embedded JSON fallback.
- `--debug-html` writes fetched pages to `debug/{site}.html` to help tune CSS selectors.
- Respect each website's terms of service and robots.txt before scraping.
