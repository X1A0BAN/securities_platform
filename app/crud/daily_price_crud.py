from __future__ import annotations

from datetime import date

from sqlalchemy import Select, desc, select
from sqlalchemy.orm import Session

from app.models.daily_price_model import DailyPrice


def get_latest_trade_date(session: Session) -> date | None:
    statement = select(DailyPrice.trade_date).order_by(DailyPrice.trade_date.desc()).limit(1)
    return session.execute(statement).scalar_one_or_none()


def list_recent_prices(session: Session, ts_code: str, limit: int = 60) -> list[DailyPrice]:
    statement: Select[tuple[DailyPrice]] = (
        select(DailyPrice)
        .where(DailyPrice.ts_code == ts_code)
        .order_by(DailyPrice.trade_date.desc())
        .limit(limit)
    )
    return list(session.execute(statement).scalars())


def list_top_gainers(
    session: Session,
    trade_date: date,
    limit: int = 50,
) -> list[DailyPrice]:
    statement: Select[tuple[DailyPrice]] = (
        select(DailyPrice)
        .where(DailyPrice.trade_date == trade_date)
        .order_by(desc(DailyPrice.pct_chg), DailyPrice.ts_code.asc())
        .limit(limit)
    )
    return list(session.execute(statement).scalars())
