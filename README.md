# 🚀 LinkedIn Job Collection & Analysis System

![LinkedIn Job Scraper](https://img.shields.io/badge/Status-Active-brightgreen.svg)
![Python](https://img.shields.io/badge/Python-3.12+-blue.svg)
![Next.js](https://img.shields.io/badge/Next.js-Frontend-black.svg)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-Database-blue.svg)
![Apify](https://img.shields.io/badge/Apify-Scraping-yellow.svg)

A professional, enterprise-grade automated pipeline for collecting, storing, and analyzing LinkedIn job postings without direct scraping limits. This system integrates Python for the backend processing, PostgreSQL for robust data storage, Apify's actor ecosystem for scraping, and a sleek modern Next.js dashboard.

---

## 🏗️ Architecture & Features

- **Automated Scraping**: Uses Apify's actor system to securely fetch job postings.
- **Robust Database**: PostgreSQL backend to store, query, and analyze jobs historically.
- **Modern Dashboard**: A Next.js frontend (`/frontend`) for visualizing data, monitoring health, and scheduling tasks.
- **Dynamic Scheduling**: Configurable intervals for autonomous job collection.
- **Clean Exporting**: Built-in support to export scraped data to CSV and Excel.

## 📂 Project Structure

```
├── app/               # Python application logic (Backend)
├── frontend/          # Next.js web application (Frontend)
├── sql/               # Database schemas and migrations
├── scripts/           # Operational & deployment scripts
├── data/              # Exported CSVs and Excel files
├── logs/              # Application runtime logs
└── requirements.txt   # Python dependencies
```

> **Note**: Test and demo files have been intentionally excluded from this repository to ensure a clean, production-ready clone experience.

---

## ⚡ Getting Started

Follow these instructions to get the system running perfectly on your local machine.

### 1. Prerequisites
- Python 3.12+
- Node.js 18+ (for frontend)
- PostgreSQL Server installed and running

### 2. Environment Setup

Copy the example environment configuration and fill in your credentials.
**Do not commit your `.env` file to version control.**

```bash
cp .env.example .env
```

Open `.env` and configure your settings:
- `APIFY_TOKEN` & `APIFY_ACTOR_ID`
- `POSTGRES_*` (Database credentials)
- `SCHEDULE_INTERVAL` & `MAX_RESULTS`

### 3. Backend Setup

Initialize the virtual environment and install dependencies:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install --upgrade pip
pip install -r requirements.txt
```

Verify the environment configuration:
```powershell
python -m app.config_validator
```

### 4. Frontend Setup

Open a new terminal window, navigate to the frontend directory, and start the Next.js app:

```bash
cd frontend
npm install
npm run dev
```

Your modern dashboard will be live at `http://localhost:3000`.

---

## 🛡️ Best Practices & Security

- **Secrets Management**: All sensitive data (Tokens, DB Passwords) is loaded dynamically via the `.env` file. Never hardcode credentials.
- **Clean Architecture**: The codebase is strictly divided into backend services and frontend presentation for maximum scalability.
- **Production Ready**: Demo, cache, and test folders are strictly `.gitignore`'d to keep the repository lightweight and professional.

## 🤝 Contribution Guidelines
When cloning this repository for team development, please ensure you branch out from `master`, run the linter configurations defined in the respective directories, and test locally before issuing a Pull Request.

---
*Built with passion for data-driven decisions.*
