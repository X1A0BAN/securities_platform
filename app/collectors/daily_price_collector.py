from __future__ import annotations

import time
from datetime import date, timedelta

import pandas as pd
import tushare as ts
from dateutil.relativedelta import relativedelta

from app.config import get_settings
from app.utils.date_utils import to_tushare_date


class TushareDailyPriceCollector:
    def __init__(self, token: str | None = None) -> None:
        settings = get_settings()
        self.token = token or settings.tushare_token
        if not self.token:
            raise ValueError(
                "Missing TUSHARE_TOKEN. Set the environment variable or pass --token to the script."
            )

        self.pro = ts.pro_api(self.token)
        self.pause_seconds = settings.tushare_pause_seconds
        self.hs300_index_code = settings.hs300_index_code

    def get_hs300_constituents(self, as_of_date: date | None = None) -> pd.DataFrame:
        target_date = as_of_date or date.today()

        for month_offset in range(0, 6):
            month_anchor = target_date - relativedelta(months=month_offset)
            month_start = month_anchor.replace(day=1)
            month_end = month_start + relativedelta(months=1) - timedelta(days=1)
            if month_offset == 0:
                month_end = min(month_end, target_date)

            weights = self.pro.index_weight(
                index_code=self.hs300_index_code,
                start_date=to_tushare_date(month_start),
                end_date=to_tushare_date(month_end),
            )
            time.sleep(self.pause_seconds)

            if weights is None or weights.empty:
                continue

            latest_trade_date = weights["trade_date"].max()
            latest_snapshot = (
                weights.loc[weights["trade_date"] == latest_trade_date]
                .sort_values("con_code")
                .reset_index(drop=True)
            )
            return latest_snapshot

        raise RuntimeError("Unable to fetch a recent HS300 constituent snapshot from Tushare.")

    def get_stock_basics(self, ts_codes: list[str]) -> pd.DataFrame:
        basics = self.pro.stock_basic(
            exchange="",
            list_status="L",
            fields="ts_code,symbol,name,area,industry,market,list_date",
        )
        time.sleep(self.pause_seconds)

        if basics is None or basics.empty:
            return pd.DataFrame()

        return basics.loc[basics["ts_code"].isin(ts_codes)].copy()

    def fetch_daily_prices(
        self,
        ts_code: str,
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        daily_prices = self.pro.daily(
            ts_code=ts_code,
            start_date=to_tushare_date(start_date),
            end_date=to_tushare_date(end_date),
        )
        time.sleep(self.pause_seconds)

        if daily_prices is None or daily_prices.empty:
            return pd.DataFrame()

        return daily_prices.sort_values("trade_date").reset_index(drop=True)

    def fetch_adj_factors(
        self,
        ts_code: str,
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        adj_factors = self.pro.adj_factor(
            ts_code=ts_code,
            start_date=to_tushare_date(start_date),
            end_date=to_tushare_date(end_date),
        )
        time.sleep(self.pause_seconds)

        if adj_factors is None or adj_factors.empty:
            return pd.DataFrame()

        return adj_factors.sort_values("trade_date").reset_index(drop=True)
