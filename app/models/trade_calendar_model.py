from __future__ import annotations

from sqlalchemy import Boolean, Column, Date, DateTime, Integer, String, UniqueConstraint, func

from app.db import Base


class TradeCalendar(Base):
    __tablename__ = "dim_trade_calendar"
    __table_args__ = (
        UniqueConstraint("trade_date", "exchange", name="uq_trade_calendar_exchange_date"),
    )

    trade_date = Column(Date, primary_key=True, nullable=False)
    exchange = Column(String(10), primary_key=True, nullable=False)
    is_open = Column(Boolean, nullable=False, default=False, server_default="0")
    pretrade_date = Column(Date, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
