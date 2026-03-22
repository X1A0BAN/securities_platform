from __future__ import annotations

from sqlalchemy import Column, Date, DateTime, Float, Index, Integer, String, UniqueConstraint, func

from app.db import Base


class AdjFactor(Base):
    __tablename__ = "fact_adj_factor"
    __table_args__ = (
        UniqueConstraint("ts_code", "trade_date", name="uq_adj_factor_code_date"),
        Index("ix_adj_factor_trade_date", "trade_date"),
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), nullable=False, index=True)
    trade_date = Column(Date, nullable=False)
    adj_factor = Column(Float, nullable=True)
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
