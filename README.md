Sentiment Analyzer API

This repository contains a small REST API for text cleaning and sentiment analysis.

Overview

The API provides endpoints to analyze text using a simple pipeline that performs:

- text cleaning (lowercasing and basic punctuation/bracket removal),
- optional lemmatization and stopword removal via spaCy (en_core_web_sm),
- sentiment scoring using VADER (neg/neu/pos/compound),
- persistence of results to a database (SQLite by default, configurable via `DATABASE_URL`).

Key points

- Lightweight endpoints designed for short-text requests.
- The spaCy model is loaded lazily on first use to reduce the startup memory peak.
- Clients do not need to provide `request_id`; the API manages identifiers.
- Default local database is `./sentiment_analyzer.db`. For production, set `DATABASE_URL` to a managed database.

Requirements

- Python 3.11 is strongly recommended (higher versions may cause compatibility issues with SQLAlchemy)
- Install dependencies:

```bash
python -m venv .venv
# On Windows PowerShell: .\.venv\Scripts\Activate.ps1
# On Windows CMD: .\.venv\Scripts\activate.bat
# On macOS/Linux: source .venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
```

Run locally

1. Optionally set `DATABASE_URL` to use a database other than SQLite. If not set, the app uses the local SQLite file.
2. Start the server with uvicorn (development mode):

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

3. Open the interactive API docs provided by FastAPI:

- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc

Main endpoints

1. POST /api/v1/analyze-single

Description: analyzes a single text string and returns the cleaned text plus VADER sentiment scores.

Request JSON example:

```json
{ "text": "I really like this product." }
```

Curl example:

```bash
curl -X POST https://<your-host>/api/v1/analyze-single \
  -H "Content-Type: application/json" \
  -d '{"text":"I really like this product."}'
```

Python example (requests):

```python
import requests

url = "https://<your-host>/api/v1/analyze-single"
resp = requests.post(url, json={"text": "I really like this product."}, timeout=20)
print(resp.status_code)
print(resp.json())
```

Example response (schema `AnalysisResult`):

```json
{
  "original_text": "I really like this product.",
  "cleaned_text": "like product",
  "sentiment_neg": 0.0,
  "sentiment_neu": 0.5,
  "sentiment_pos": 0.5,
  "sentiment_compound": 0.6696
}
```

2. POST /api/v1/analyze-batch

Description: analyzes a list of text objects and returns a list of results in the same order as the input.

Request JSON example:

```json
[{ "text": "I love this!" }, { "text": "Not good at all." }]
```

The response is a list of `AnalysisResult` objects. Each input item is validated for the `text` field and minimum length.

Environment variables and database

- `DATABASE_URL`: SQLAlchemy connection string. If not provided, the app uses `sqlite:///./sentiment_analyzer.db`.
- For local development you can place environment variables in a `.env` file; the project uses `python-dotenv` to load them.

Deployment notes

- Render: if deploying to Render, ensure the service uses Python 3.11 (via `runtime.txt`, the Render UI, or a manifest). Use the smallest runtime that meets your memory needs.
- Memory note: spaCy and some NLP libraries can consume significant RAM. For small plans (e.g. 512 MB) either use lazy-loading (already implemented) or upgrade the instance.
