# 用途：兼容旧的行情查询入口，内部转发到单股查询和市场排行服务。
from __future__ import annotations

from datetime import date
from typing import Any

from app.services.ranking_service import RankingService
from app.services.single_stock_service import SingleStockService


class MarketQueryService:
    def __init__(
        self,
        single_stock_service: SingleStockService | None = None,
        ranking_service: RankingService | None = None,
    ) -> None:
        self._single_stock_service = single_stock_service or SingleStockService()
        self._ranking_service = ranking_service or RankingService()

    def get_recent_prices(self, ts_code: str, days: int = 60) -> dict[str, Any]:
        return self._single_stock_service.get_recent_prices(ts_code=ts_code, days=days)

    def get_top_gainers(
        self,
        limit: int = 50,
        trade_date: date | None = None,
    ) -> dict[str, Any]:
        return self._ranking_service.get_top_gainers(limit=limit, trade_date=trade_date)
