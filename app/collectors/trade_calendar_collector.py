from __future__ import annotations

import time
from datetime import date

import pandas as pd
import tushare as ts

from app.config import get_settings
from app.utils.date_utils import to_tushare_date


EXCHANGE_CODE_MAP = {
    "SSE": "SH",
    "SZSE": "SZ",
    "BSE": "BJ",
}


class TushareTradeCalendarCollector:
    def __init__(self, token: str | None = None) -> None:
        settings = get_settings()
        self.token = token or settings.tushare_token
        if not self.token:
            raise ValueError(
                "缺少 TUSHARE_TOKEN。请设置环境变量，或在脚本里通过 --token 传入。"
            )

        self.pro = ts.pro_api(self.token)
        self.pause_seconds = settings.tushare_pause_seconds

    def fetch_trade_calendar(
        self,
        exchange: str,
        start_date: date,
        end_date: date,
    ) -> pd.DataFrame:
        trade_calendar = self.pro.trade_cal(
            exchange=exchange,
            start_date=to_tushare_date(start_date),
            end_date=to_tushare_date(end_date),
        )
        time.sleep(self.pause_seconds)

        if trade_calendar is None or trade_calendar.empty:
            return pd.DataFrame()

        normalized = trade_calendar.copy()
        normalized["exchange"] = normalized["exchange"].map(
            lambda value: EXCHANGE_CODE_MAP.get(value, value)
        )
        return normalized.sort_values(["exchange", "cal_date"]).reset_index(drop=True)
