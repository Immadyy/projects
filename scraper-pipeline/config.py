import os

from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.environ["DATABASE_URL"]
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
SCRAPE_PAGES = int(os.getenv("SCRAPE_PAGES", "5"))
SCRAPE_API_KEY = os.getenv("SCRAPE_API_KEY")
