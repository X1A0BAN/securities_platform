# 用途：负责市场级榜单查询，例如涨幅榜、跌幅榜等排行能力。
from __future__ import annotations

from datetime import date
from typing import Any

from app.cache import TTLCache, get_query_cache
from app.crud.daily_price_crud import get_latest_trade_date, list_top_gainers
from app.db import session_scope


class RankingService:
    def __init__(self, cache: TTLCache | None = None) -> None:
        self._cache = cache or get_query_cache()

    def get_top_gainers(
        self,
        limit: int = 50,
        trade_date: date | None = None,
    ) -> dict[str, Any]:
        cache_key = f"top_gainers:{trade_date}:{limit}"
        cached_result = self._cache.get(cache_key)
        if cached_result is not None:
            return cached_result

        with session_scope() as session:
            effective_trade_date = trade_date or get_latest_trade_date(session)
            if effective_trade_date is None:
                result = {"trade_date": None, "limit": limit, "rows": []}
                return self._cache.set(cache_key, result)

            rows = list_top_gainers(
                session,
                trade_date=effective_trade_date,
                limit=limit,
            )
            serialized_rows = [self._serialize_daily_price(row) for row in rows]

        result = {
            "trade_date": effective_trade_date.isoformat(),
            "limit": limit,
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
