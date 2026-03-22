from __future__ import annotations

from datetime import date, datetime

from dateutil.relativedelta import relativedelta


def parse_date(value: str) -> date:
    cleaned = value.strip()
    if "-" in cleaned:
        return date.fromisoformat(cleaned)
    return datetime.strptime(cleaned, "%Y%m%d").date()


def to_tushare_date(value: date) -> str:
    return value.strftime("%Y%m%d")


def years_ago(reference_date: date, years: int) -> date:
    return reference_date - relativedelta(years=years)
