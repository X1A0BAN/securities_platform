from __future__ import annotations

import time
from datetime import date

import pandas as pd
import tushare as ts

from app.config import get_settings
from app.utils.date_utils import to_tushare_date


class TushareDailyPriceCollector:
    def __init__(self, token: str | None = None) -> None:
        settings = get_settings()
        self.token = token or settings.tushare_token
        if not self.token:
            raise ValueError(
                "缺少 TUSHARE_TOKEN。请设置环境变量，或在脚本里通过 --token 传入。"
            )

        self.pro = ts.pro_api(self.token)
        self.pause_seconds = settings.tushare_pause_seconds

    def fetch_daily_prices_by_trade_date(self, trade_date: date) -> pd.DataFrame:
        # 对当前这种批量同步场景，按交易日整市场抓取会比逐只股票循环抓取更高效。
        daily_prices = self.pro.daily(trade_date=to_tushare_date(trade_date))
        time.sleep(self.pause_seconds)

        if daily_prices is None or daily_prices.empty:
            return pd.DataFrame()

        return daily_prices.reset_index(drop=True)

    def fetch_adj_factors_by_trade_date(self, trade_date: date) -> pd.DataFrame:
        adj_factors = self.pro.adj_factor(trade_date=to_tushare_date(trade_date))
        time.sleep(self.pause_seconds)

        if adj_factors is None or adj_factors.empty:
            return pd.DataFrame()

        return adj_factors.reset_index(drop=True)
