import re
from datetime import date, datetime, timedelta
from dateutil import parser as date_parser


def parse_relative_date(date_str: str):
    """
    Parses both absolute dates and relative strings (e.g., '2 months ago', 'today').
    """
    if not date_str:
        return None

    cleaned = date_str.strip().lower()
    today = date.today()

    if 'today' in cleaned:
        return today
    if 'yesterday' in cleaned:
        return today - timedelta(days=1)

    # Relative days, months, years
    match_days = re.search(r'(\d+)\s+days?\s+ago', cleaned)
    if match_days:
        return today - timedelta(days=int(match_days.group(1)))

    match_months = re.search(r'(\d+)\s+months?\s+ago', cleaned)
    if match_months:
        return today - timedelta(days=int(match_months.group(1)) * 30)

    match_years = re.search(r'(\d+)\s+years?\s+ago', cleaned)
    if match_years:
        return today - timedelta(days=int(match_years.group(1)) * 365)

    try:
        return date_parser.parse(date_str, fuzzy=True).date()
    except Exception:
        return None


def clean_price_string(price_raw) -> float:
    """Removes currency symbols (₹, $, commas) and parses float."""
    if not price_raw:
        return 0.0
    digits = re.sub(r'[^\d.]', '', str(price_raw))
    try:
        return float(digits)
    except ValueError:
        return 0.0