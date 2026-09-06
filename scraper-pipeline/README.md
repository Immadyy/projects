# Quote Scraper API

A FastAPI service that scrapes quotes with Playwright and stores them in PostgreSQL.

## Local setup

Create the environment file from the template:

```bash
cp .env.example .env
```

Edit `.env` and replace `your_password` with your local PostgreSQL password.

Create and activate the virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
playwright install chromium
```

Start the API:

```bash
python main.py
```

Trigger a scrape:

```bash
curl -X POST http://127.0.0.1:8000/api/scrape/quotes
```

The endpoint returns `202` immediately. The scraper continues in the background.

Read stored quotes:

```bash
curl "http://127.0.0.1:8000/api/quotes?limit=50&offset=0"
```

The response is paginated and includes `total`, `has_more`, and `next_offset`.
Use `next_offset` for the next request until `has_more` is `false`. The API
limits each response to 100 quotes, so a client never has to download an
unbounded response.

## Docker

Build and run the image with a local `.env` file:

```bash
docker build -t quote-scraper .
docker run --env-file .env -p 8000:8000 quote-scraper
```

## Render

Create a PostgreSQL database and a web service from this repository. Add the database's internal connection string as the `DATABASE_URL` environment variable in the Render dashboard. Render provides `PORT` automatically; the application listens on it.

Do not commit `.env`. Only `.env.example` belongs in the repository.

## Project layout

- `main.py`: FastAPI application, lifecycle, and API route
- `config.py`: environment configuration
- `database.py`: PostgreSQL pool and table setup
- `models.py`: Pydantic validation model
- `scraper.py`: Playwright scraping and database inserts
