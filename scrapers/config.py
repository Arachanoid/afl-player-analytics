import os

START_YEAR = 2012
END_YEAR = 2026

AFLTABLES_STATS_URL = "https://afltables.com/afl/stats/{year}.html"
AFLTABLES_GAMES_URL = "https://afltables.com/afl/seas/{year}.html"

SQUIGGLE_BASE_URL = "https://api.squiggle.com.au/"
SQUIGGLE_USER_AGENT = "AFL-Analytics-Portfolio/1.0 (deanmathew2000@gmail.com)"

REQUEST_DELAY_SECONDS = 2   # polite delay between AFL Tables requests
REQUEST_TIMEOUT = 30

# Paths are always relative to the project root (one level up from scrapers/)
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RAW_DATA_DIR     = os.path.join(_PROJECT_ROOT, "data", "raw")
CLEANED_DATA_DIR = os.path.join(_PROJECT_ROOT, "data", "cleaned")
DATABASE_PATH    = os.path.join(_PROJECT_ROOT, "data", "database", "afl_analytics.db")
