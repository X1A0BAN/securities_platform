from __future__ import annotations

import time

import pandas as pd
import tushare as ts

from app.config import get_settings


SUPPORTED_MAIN_BOARD_EXCHANGES = {"SSE", "SZSE"}
SUPPORTED_MAIN_BOARD_MARKETS = {"\u4e3b\u677f"}


class TushareStockBasicCollector:
    def __init__(self, token: str | None = None) -> None:
        settings = get_settings()
        self.token = token or settings.tushare_token
        if not self.token:
            raise ValueError(
                "缺少 TUSHARE_TOKEN。请设置环境变量，或在脚本里通过 --token 传入。"
            )

        self.pro = ts.pro_api(self.token)
        self.pause_seconds = settings.tushare_pause_seconds

    def fetch_stock_basics(self, list_status: str) -> pd.DataFrame:
        stock_basics = self.pro.stock_basic(
            exchange="",
            list_status=list_status,
            fields="ts_code,symbol,name,market,exchange,industry,list_date,delist_date,list_status",
        )
        time.sleep(self.pause_seconds)

        if stock_basics is None or stock_basics.empty:
            return pd.DataFrame()

        return stock_basics.reset_index(drop=True)

    def fetch_main_board_stock_universe(self) -> pd.DataFrame:
        frames: list[pd.DataFrame] = []
        for list_status in ("L", "D"):
            frame = self.fetch_stock_basics(list_status=list_status)
            if frame is not None and not frame.empty:
                frames.append(frame)

        if not frames:
            return pd.DataFrame()

        # 先把上市和退市股票都拉下来，再交给服务层按同步时间范围裁剪。
        merged = pd.concat(frames, ignore_index=True)
        filtered = merged.loc[
            merged["exchange"].isin(SUPPORTED_MAIN_BOARD_EXCHANGES)
            & merged["market"].isin(SUPPORTED_MAIN_BOARD_MARKETS)
        ].copy()
        return filtered.sort_values("ts_code").reset_index(drop=True)
