from __future__ import annotations

from sqlalchemy import Column, Date, DateTime, Float, Index, Integer, String, UniqueConstraint, func

from app.db import Base


class DailyPrice(Base):
    __tablename__ = "fact_daily_price"
    __table_args__ = (
        UniqueConstraint("ts_code", "trade_date", name="uq_daily_price_code_date"),
        Index("ix_daily_price_trade_date", "trade_date"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), nullable=False, index=True)
    trade_date = Column(Date, nullable=False)
    open = Column(Float, nullable=True)
    high = Column(Float, nullable=True)
    low = Column(Float, nullable=True)
    close = Column(Float, nullable=True)
    pre_close = Column(Float, nullable=True)
    change_amount = Column(Float, nullable=True)
    pct_chg = Column(Float, nullable=True)
    vol = Column(Integer, nullable=True)
    amount = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
