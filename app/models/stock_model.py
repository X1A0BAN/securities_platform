from __future__ import annotations

from sqlalchemy import Boolean, Column, Date, DateTime, Integer, String, func

from app.db import Base


class Stock(Base):
    __tablename__ = "dim_stock"

    id = Column(Integer, primary_key=True, autoincrement=True)
    ts_code = Column(String(20), nullable=False, unique=True, index=True)
    symbol = Column(String(10), nullable=False, index=True)
    name = Column(String(50), nullable=False, index=True)
    market = Column(String(20), nullable=True)
    exchange = Column(String(10), nullable=True, index=True)
    industry = Column(String(100), nullable=True)
    list_date = Column(Date, nullable=True)
    delist_date = Column(Date, nullable=True)
    is_active = Column(Boolean, nullable=False, default=True, server_default="1")
    created_at = Column(DateTime, nullable=False, server_default=func.now())
    updated_at = Column(DateTime, nullable=False, server_default=func.now(), onupdate=func.now())
