from __future__ import annotations

from sqlalchemy import Select, select
from sqlalchemy.orm import Session

from app.models.stock_model import Stock


def get_stock_by_code(session: Session, ts_code: str) -> Stock | None:
    statement = select(Stock).where(Stock.ts_code == ts_code)
    return session.execute(statement).scalar_one_or_none()


def list_active_stocks(session: Session) -> list[Stock]:
    statement: Select[tuple[Stock]] = (
        select(Stock)
        .where(Stock.is_active.is_(True))
        .order_by(Stock.ts_code.asc())
    )
    return list(session.execute(statement).scalars())


def list_stocks_by_industry(session: Session, industry: str) -> list[Stock]:
    statement: Select[tuple[Stock]] = (
        select(Stock)
        .where(Stock.industry == industry)
        .where(Stock.is_active.is_(True))
        .order_by(Stock.ts_code.asc())
    )
    return list(session.execute(statement).scalars())
