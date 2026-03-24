# 用途：作为股票分析总入口，统一组合单股、排行、指标、选股和板块服务。
from __future__ import annotations

from datetime import date
from typing import Any

from app.services.indicator_service import IndicatorService
from app.services.ranking_service import RankingService
from app.services.screener_service import ScreenerService
from app.services.sector_service import SectorService
from app.services.single_stock_service import SingleStockService


class StockAnalysisService:
    def __init__(
        self,
        single_stock_service: SingleStockService | None = None,
        ranking_service: RankingService | None = None,
        indicator_service: IndicatorService | None = None,
        screener_service: ScreenerService | None = None,
        sector_service: SectorService | None = None,
    ) -> None:
        self.single_stock = single_stock_service or SingleStockService()
        self.ranking = ranking_service or RankingService()
        self.indicator = indicator_service or IndicatorService()
        self.screener = screener_service or ScreenerService()
        self.sector = sector_service or SectorService()

    def get_recent_prices(self, ts_code: str, days: int = 60) -> dict[str, Any]:
        return self.single_stock.get_recent_prices(ts_code=ts_code, days=days)

    def get_top_gainers(
        self,
        limit: int = 50,
        trade_date: date | None = None,
    ) -> dict[str, Any]:
        return self.ranking.get_top_gainers(limit=limit, trade_date=trade_date)

    def get_recent_prices_with_ma(
        self,
        ts_code: str,
        days: int = 60,
        window: int = 20,
    ) -> dict[str, Any]:
        result = self.single_stock.get_recent_prices(ts_code=ts_code, days=days)
        result["rows"] = self.indicator.calculate_simple_moving_average(
            rows=result["rows"],
            window=window,
        )
        result["indicator"] = f"ma_{window}"
        return result
