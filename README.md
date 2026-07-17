# LinkedIn Job Collection System

This workspace contains the initial Stage 1 scaffold for a production-oriented job collection pipeline that uses Python, PostgreSQL, and the Apify LinkedIn Jobs Scraper Actor without scraping LinkedIn directly.

## Stage 1 Deliverables
- Workspace scan completed
- Python verified: Python 3.12.10
- PostgreSQL CLI verification was not possible in this environment because `psql`, `pg_isready`, and `postgres` were not available on PATH
- Initial project structure created
- Python dependencies declared in requirements.txt

## Proposed Structure
- app/ for application code
- sql/ for database schema files
- scripts/ for operational helpers
- .env.example for environment placeholders

## Next Step
Review this scaffold and approve Stage 2 when ready.

## Stage 2: Python environment & dependency setup

1. Create and activate a virtual environment (Windows PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

2. Upgrade pip and install dependencies:

```powershell
.\.venv\Scripts\python -m pip install --upgrade pip setuptools wheel
.\.venv\Scripts\python -m pip install -r requirements.txt
```

3. Verify dependencies:

```powershell
.\.venv\Scripts\python scripts/check_dependencies.py
```

The `check_dependencies.py` script imports each required package, prints the installed version, and exits with code 0 when all packages are present.

## Stage 3: Environment configuration & validation

1. Copy `.env.example` to `.env` and populate secrets:

```powershell
copy .env.example .env
```

2. Edit `.env` and fill in required values:

- `APIFY_TOKEN`
- `APIFY_ACTOR_ID`
- `POSTGRES_HOST`
- `POSTGRES_PORT`
- `POSTGRES_DB`
- `POSTGRES_USER`
- `POSTGRES_PASSWORD`
- `CSV_EXPORT_PATH`
- `EXCEL_EXPORT_PATH`
- `LOG_LEVEL`
- `LOG_PATH`
- `MAX_RESULTS`
- `SCHEDULE_INTERVAL`

3. Validate configuration and runtime connectivity:

```powershell
.\.venv\Scripts\python -m app.config_validator
```

This validation module checks environment values, verifies Apify authentication, verifies PostgreSQL connectivity, and creates required directories.

### Configuration details

- `APIFY_TOKEN`: Apify API token used for authentication
- `APIFY_ACTOR_ID`: Actor ID for the Apify LinkedIn Jobs Scraper Actor
- `POSTGRES_HOST`: PostgreSQL host name or IP
- `POSTGRES_PORT`: PostgreSQL port number
- `POSTGRES_DB`: PostgreSQL target database name
- `POSTGRES_USER`: PostgreSQL username
- `POSTGRES_PASSWORD`: PostgreSQL password
- `CSV_EXPORT_PATH`: path to generate CSV exports
- `EXCEL_EXPORT_PATH`: path to generate Excel exports
- `LOG_LEVEL`: logging threshold (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- `LOG_PATH`: path to the application log file
- `MAX_RESULTS`: maximum number of jobs to fetch
- `SCHEDULE_INTERVAL`: interval for scheduled job collection

