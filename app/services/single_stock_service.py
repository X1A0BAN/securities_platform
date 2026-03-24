# 用途：负责单只股票的基础查询，例如最近 N 天行情。
from __future__ import annotations

from typing import Any

from app.cache import TTLCache, get_query_cache
from app.crud.daily_price_crud import list_recent_prices
from app.crud.stock_crud import get_stock_by_code
from app.db import session_scope


class SingleStockService:
    def __init__(self, cache: TTLCache | None = None) -> None:
        self._cache = cache or get_query_cache()

    def get_recent_prices(self, ts_code: str, days: int = 60) -> dict[str, Any]:
        cache_key = f"recent_prices:{ts_code}:{days}"
        cached_result = self._cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        with session_scope() as session:
            stock = get_stock_by_code(session, ts_code)
            prices = list_recent_prices(session, ts_code=ts_code, limit=days)
            serialized_rows = [self._serialize_daily_price(row) for row in prices]
            stock_name = stock.name if stock else None

        result = {
            "ts_code": ts_code,
            "stock_name": stock_name,
            "days": days,
            "rows": serialized_rows,
        }
        return self._cache.set(cache_key, result)

    @staticmethod
    def _serialize_daily_price(row: Any) -> dict[str, Any]:
        return {
            "ts_code": row.ts_code,
            "trade_date": row.trade_date.isoformat(),
            "open": row.open,
            "high": row.high,
            "low": row.low,
            "close": row.close,
            "pre_close": row.pre_close,
            "change_amount": row.change_amount,
            "pct_chg": row.pct_chg,
            "vol": row.vol,
            "amount": row.amount,
        }
