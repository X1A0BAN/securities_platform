from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
from sqlalchemy import func, select
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.collectors.daily_price_collector import TushareDailyPriceCollector
from app.collectors.stock_basic_collector import TushareStockBasicCollector
from app.collectors.trade_calendar_collector import TushareTradeCalendarCollector
from app.db import session_scope
from app.models.adj_factor_model import AdjFactor
from app.models.daily_price_model import DailyPrice
from app.models.stock_model import Stock
from app.models.trade_calendar_model import TradeCalendar
from app.utils.date_utils import parse_date, years_ago
from app.utils.logger import get_logger


logger = get_logger(__name__)


class SyncService:
    def __init__(
        self,
        collector: TushareDailyPriceCollector | None = None,
        stock_basic_collector: TushareStockBasicCollector | None = None,
        trade_calendar_collector: TushareTradeCalendarCollector | None = None,
    ) -> None:
        self._collector = collector
        self._stock_basic_collector = stock_basic_collector
        self._trade_calendar_collector = trade_calendar_collector

    @property
    def collector(self) -> TushareDailyPriceCollector:
        # 按需初始化 collector，避免单用途脚本额外创建并不会用到的 Tushare 客户端。
        if self._collector is None:
            self._collector = TushareDailyPriceCollector()
        return self._collector

    @property
    def stock_basic_collector(self) -> TushareStockBasicCollector:
        if self._stock_basic_collector is None:
            self._stock_basic_collector = TushareStockBasicCollector()
        return self._stock_basic_collector

    @property
    def trade_calendar_collector(self) -> TushareTradeCalendarCollector:
        if self._trade_calendar_collector is None:
            self._trade_calendar_collector = TushareTradeCalendarCollector()
        return self._trade_calendar_collector

    def sync_main_board_stock_basics(
        self,
        end_date: date | None = None,
        years: int = 3,
    ) -> dict[str, object]:
        effective_end_date = end_date or date.today()
        effective_start_date = years_ago(effective_end_date, years)
        filtered_universe = self._get_filtered_main_board_universe(
            start_date=effective_start_date,
            end_date=effective_end_date,
        )

        self._upsert_main_board_stocks(filtered_universe)

        summary = {
            "stock_count": len(filtered_universe),
            "start_date": str(effective_start_date),
            "end_date": str(effective_end_date),
        }
        logger.info("Main-board stock basic sync completed: %s", summary)
        return summary

    def backfill_main_board_daily_prices(
        self,
        years: int = 3,
        end_date: date | None = None,
        start_date: date | None = None,
    ) -> dict[str, object]:
        effective_end_date = end_date or date.today()
        effective_start_date = start_date or years_ago(effective_end_date, years)
        filtered_universe = self._get_filtered_main_board_universe(
            start_date=effective_start_date,
            end_date=effective_end_date,
        )

        self._upsert_main_board_stocks(filtered_universe)
        summary = self._sync_main_board_market_data(
            filtered_universe=filtered_universe,
            start_date=effective_start_date,
            end_date=effective_end_date,
            model=DailyPrice,
            fetch_by_trade_date=self.collector.fetch_daily_prices_by_trade_date,
            payload_builder=self._build_daily_price_payloads,
            unique_columns=["ts_code", "trade_date"],
            label="main-board daily prices",
            use_stored_trade_dates=False,
        )
        logger.info("Main-board daily price backfill completed: %s", summary)
        return summary

    def backfill_main_board_adj_factors(
        self,
        years: int = 3,
        end_date: date | None = None,
        start_date: date | None = None,
    ) -> dict[str, object]:
        effective_end_date = end_date or date.today()
        effective_start_date = start_date or years_ago(effective_end_date, years)
        filtered_universe = self._get_filtered_main_board_universe(
            start_date=effective_start_date,
            end_date=effective_end_date,
        )

        summary = self._sync_main_board_market_data(
            filtered_universe=filtered_universe,
            start_date=effective_start_date,
            end_date=effective_end_date,
            model=AdjFactor,
            fetch_by_trade_date=self.collector.fetch_adj_factors_by_trade_date,
            payload_builder=self._build_adj_factor_payloads,
            unique_columns=["ts_code", "trade_date"],
            label="main-board adj factors",
            use_stored_trade_dates=False,
        )
        logger.info("Main-board adj factor backfill completed: %s", summary)
        return summary

    def sync_trade_calendar(
        self,
        years: int = 3,
        end_date: date | None = None,
        start_date: date | None = None,
        exchanges: tuple[str, ...] = ("SSE", "SZSE"),
    ) -> dict[str, object]:
        effective_end_date = end_date or date.today()
        effective_start_date = start_date or years_ago(effective_end_date, years)

        summary: dict[str, object] = {
            "start_date": str(effective_start_date),
            "end_date": str(effective_end_date),
            "rows_written": 0,
            "exchanges": [],
        }

        for exchange in exchanges:
            logger.info(
                "Fetching trade calendar for %s from %s to %s.",
                exchange,
                effective_start_date,
                effective_end_date,
            )
            trade_calendar_df = self.trade_calendar_collector.fetch_trade_calendar(
                exchange=exchange,
                start_date=effective_start_date,
                end_date=effective_end_date,
            )
            if trade_calendar_df.empty:
                logger.warning("No trade calendar data returned for %s.", exchange)
                continue

            payloads = self._build_trade_calendar_payloads(trade_calendar_df)
            with session_scope() as session:
                self._upsert_rows(
                    session,
                    TradeCalendar,
                    payloads,
                    unique_columns=["trade_date", "exchange"],
                )

            summary["rows_written"] = int(summary["rows_written"]) + len(payloads)
            cast_exchanges = summary["exchanges"]
            if isinstance(cast_exchanges, list):
                cast_exchanges.append(exchange)

        logger.info("Trade calendar sync completed: %s", summary)
        return summary

    def sync_incremental_main_board_daily_prices(
        self,
        end_date: date | None = None,
        start_date: date | None = None,
    ) -> dict[str, object]:
        effective_end_date = end_date or date.today()
        effective_start_date = start_date or self._get_incremental_start_date(
            model=DailyPrice,
            end_date=effective_end_date,
            label="main-board daily price",
        )
        filtered_universe = self._get_filtered_main_board_universe(
            start_date=effective_start_date,
            end_date=effective_end_date,
        )

        summary = self._sync_main_board_market_data(
            filtered_universe=filtered_universe,
            start_date=effective_start_date,
            end_date=effective_end_date,
            model=DailyPrice,
            fetch_by_trade_date=self.collector.fetch_daily_prices_by_trade_date,
            payload_builder=self._build_daily_price_payloads,
            unique_columns=["ts_code", "trade_date"],
            label="incremental main-board daily prices",
            use_stored_trade_dates=True,
        )
        logger.info("Incremental main-board daily price sync completed: %s", summary)
        return summary

    def sync_incremental_main_board_adj_factors(
        self,
        end_date: date | None = None,
        start_date: date | None = None,
    ) -> dict[str, object]:
        effective_end_date = end_date or date.today()
        effective_start_date = start_date or self._get_incremental_start_date(
            model=AdjFactor,
            end_date=effective_end_date,
            label="main-board adj factor",
        )
        filtered_universe = self._get_filtered_main_board_universe(
            start_date=effective_start_date,
            end_date=effective_end_date,
        )

        summary = self._sync_main_board_market_data(
            filtered_universe=filtered_universe,
            start_date=effective_start_date,
            end_date=effective_end_date,
            model=AdjFactor,
            fetch_by_trade_date=self.collector.fetch_adj_factors_by_trade_date,
            payload_builder=self._build_adj_factor_payloads,
            unique_columns=["ts_code", "trade_date"],
            label="incremental main-board adj factors",
            use_stored_trade_dates=True,
        )
        logger.info("Incremental main-board adj factor sync completed: %s", summary)
        return summary

    def run_main_board_daily_sync(
        self,
        end_date: date | None = None,
        years: int = 3,
        calendar_lookback_days: int = 30,
    ) -> dict[str, object]:
        effective_end_date = end_date or date.today()
        calendar_start_date = self._get_trade_calendar_sync_start_date(
            end_date=effective_end_date,
            years=years,
            lookback_days=calendar_lookback_days,
        )

        summary = {
            "stock_basic": self.sync_main_board_stock_basics(
                years=years,
                end_date=effective_end_date,
            ),
            "trade_calendar": self.sync_trade_calendar(
                years=0,
                start_date=calendar_start_date,
                end_date=effective_end_date,
            ),
            "daily_price": self.sync_incremental_main_board_daily_prices(
                end_date=effective_end_date,
            ),
            "adj_factor": self.sync_incremental_main_board_adj_factors(
                end_date=effective_end_date,
            ),
        }
        logger.info("Main-board daily sync completed: %s", summary)
        return summary

    def _sync_main_board_market_data(
        self,
        filtered_universe,
        start_date: date,
        end_date: date,
        model,
        fetch_by_trade_date,
        payload_builder,
        unique_columns: list[str],
        label: str,
        use_stored_trade_dates: bool,
    ) -> dict[str, object]:
        # Tushare 的日线和复权因子接口按交易日抓取更高效，因此这里先按开市日抓整市场，
        # 再在内存里筛出当前主板股票池。
        code_set = set(filtered_universe["ts_code"].tolist())
        trade_dates = self._get_trade_dates(
            start_date=start_date,
            end_date=end_date,
            use_stored_trade_dates=use_stored_trade_dates,
        )

        rows_written = 0
        for index, trade_date in enumerate(trade_dates, start=1):
            logger.info("Fetching %s %s/%s %s", label, index, len(trade_dates), trade_date)
            market_df = fetch_by_trade_date(trade_date)
            if market_df.empty:
                continue

            filtered_market_df = market_df.loc[market_df["ts_code"].isin(code_set)].copy()
            if filtered_market_df.empty:
                continue

            payloads = payload_builder(filtered_market_df)
            with session_scope() as session:
                self._upsert_rows(
                    session,
                    model,
                    payloads,
                    unique_columns=unique_columns,
                )
            rows_written += len(payloads)

        return {
            "stock_count": len(code_set),
            "trade_date_count": len(trade_dates),
            "rows_written": rows_written,
            "start_date": str(start_date),
            "end_date": str(end_date),
        }

    def _get_filtered_main_board_universe(self, start_date: date, end_date: date):
        universe = self.stock_basic_collector.fetch_main_board_stock_universe()
        if universe.empty:
            raise RuntimeError("Tushare 没有返回主板股票基础数据。")
        return self._filter_universe_for_date_range(
            universe=universe,
            start_date=start_date,
            end_date=end_date,
        )

    def _get_trade_dates(
        self,
        start_date: date,
        end_date: date,
        use_stored_trade_dates: bool,
    ) -> list[date]:
        trade_dates = []
        if use_stored_trade_dates:
            # 增量同步优先使用库里已经规范化过的交易日历；
            # 如果交易日历表还没有数据，再回退到直接请求 Tushare。
            trade_dates = self._get_stored_open_trade_dates(
                start_date=start_date,
                end_date=end_date,
            )

        if trade_dates:
            return trade_dates

        return self._get_open_trade_dates(
            start_date=start_date,
            end_date=end_date,
        )

    def _build_daily_price_payloads(self, price_df) -> list[dict[str, object]]:
        return [
            {
                "ts_code": row.ts_code,
                "trade_date": parse_date(row.trade_date),
                "open": self._to_optional_float(row.open),
                "high": self._to_optional_float(row.high),
                "low": self._to_optional_float(row.low),
                "close": self._to_optional_float(row.close),
                "pre_close": self._to_optional_float(row.pre_close),
                "change_amount": self._to_optional_float(row.change),
                "pct_chg": self._to_optional_float(row.pct_chg),
                "vol": self._to_optional_int(row.vol),
                "amount": self._to_optional_float(row.amount),
            }
            for row in price_df.itertuples(index=False)
        ]

    def _build_adj_factor_payloads(self, adj_factor_df) -> list[dict[str, object]]:
        return [
            {
                "ts_code": row.ts_code,
                "trade_date": parse_date(row.trade_date),
                "adj_factor": self._to_optional_float(row.adj_factor),
            }
            for row in adj_factor_df.itertuples(index=False)
        ]

    def _build_trade_calendar_payloads(self, trade_calendar_df) -> list[dict[str, object]]:
        return [
            {
                "trade_date": parse_date(row.cal_date),
                "exchange": row.exchange,
                "is_open": bool(row.is_open),
                "pretrade_date": (
                    parse_date(str(row.pretrade_date))
                    if pd.notna(row.pretrade_date) and str(row.pretrade_date).strip() != ""
                    else None
                ),
            }
            for row in trade_calendar_df.itertuples(index=False)
        ]

    def _build_stock_payloads_from_basics(self, basics_df) -> list[dict[str, object]]:
        return [
            {
                "ts_code": row.ts_code,
                "symbol": row.symbol,
                "name": row.name,
                "industry": row.industry,
                "market": row.market,
                "exchange": "SH" if row.exchange == "SSE" else "SZ",
                "list_date": parse_date(str(row.list_date)) if pd.notna(row.list_date) else None,
                "delist_date": parse_date(str(row.delist_date)) if pd.notna(row.delist_date) else None,
                "is_active": row.list_status == "L",
            }
            for row in basics_df.itertuples(index=False)
        ]

    def _upsert_main_board_stocks(self, basics_df) -> None:
        payloads = self._build_stock_payloads_from_basics(basics_df)
        with session_scope() as session:
            self._upsert_rows(session, Stock, payloads, unique_columns=["ts_code"])

    def _filter_universe_for_date_range(self, universe, start_date: date, end_date: date):
        if universe is None or universe.empty:
            return pd.DataFrame()

        # 只保留在同步结束日之前已经上市，且没有在同步窗口开始前退市的股票。
        list_dates = pd.to_datetime(universe["list_date"], format="%Y%m%d", errors="coerce").dt.date
        delist_dates = pd.to_datetime(universe["delist_date"], format="%Y%m%d", errors="coerce").dt.date
        return (
            universe.loc[
                (list_dates <= end_date)
                & (delist_dates.isna() | (delist_dates >= start_date))
            ]
            .copy()
            .sort_values("ts_code")
            .reset_index(drop=True)
        )

    def _get_open_trade_dates(self, start_date: date, end_date: date) -> list[date]:
        open_dates = set()
        for exchange in ("SSE", "SZSE"):
            calendar_df = self.trade_calendar_collector.fetch_trade_calendar(
                exchange=exchange,
                start_date=start_date,
                end_date=end_date,
            )
            if calendar_df.empty:
                continue

            open_rows = calendar_df.loc[calendar_df["is_open"] == 1]
            open_dates.update(parse_date(value) for value in open_rows["cal_date"].tolist())

        return sorted(open_dates)

    def _get_stored_open_trade_dates(self, start_date: date, end_date: date) -> list[date]:
        with session_scope() as session:
            rows = session.execute(
                select(TradeCalendar.trade_date)
                .where(TradeCalendar.trade_date >= start_date)
                .where(TradeCalendar.trade_date <= end_date)
                .where(TradeCalendar.exchange.in_(("SH", "SZ")))
                .where(TradeCalendar.is_open.is_(True))
                .distinct()
                .order_by(TradeCalendar.trade_date)
            ).scalars().all()
        return list(rows)

    def _get_latest_trade_date(self, model) -> date | None:
        with session_scope() as session:
            return session.execute(select(func.max(model.trade_date))).scalar_one()

    def _get_incremental_start_date(self, model, end_date: date, label: str) -> date:
        latest_trade_date = self._get_latest_trade_date(model)
        if latest_trade_date is None:
            raise RuntimeError(
                f"数据库里还没有 {label} 数据。"
                "请先执行最近三年的全量回补，再使用每日增量同步。"
            )
        # 从下一自然日开始即可，后续的开市日过滤会自动排除周末和节假日。
        return latest_trade_date + timedelta(days=1)

    def _get_latest_trade_calendar_date(self) -> date | None:
        with session_scope() as session:
            return session.execute(select(func.max(TradeCalendar.trade_date))).scalar_one()

    def _get_trade_calendar_sync_start_date(
        self,
        end_date: date,
        years: int,
        lookback_days: int,
    ) -> date:
        latest_trade_calendar_date = self._get_latest_trade_calendar_date()
        if latest_trade_calendar_date is None:
            return years_ago(end_date, years)

        buffered_start_date = latest_trade_calendar_date - timedelta(days=max(lookback_days, 0))
        return min(end_date, buffered_start_date)

    def _upsert_rows(
        self,
        session,
        model,
        rows: list[dict[str, object]],
        unique_columns: list[str],
    ) -> None:
        if not rows:
            return

        dialect_name = session.bind.dialect.name
        if dialect_name == "sqlite":
            statement = sqlite_insert(model).values(rows)
            excluded = statement.excluded
            update_columns = {
                column.name: getattr(excluded, column.name)
                for column in model.__table__.columns
                if column.name not in {"id", "created_at", "updated_at", *unique_columns}
            }
            statement = statement.on_conflict_do_update(
                index_elements=unique_columns,
                set_=update_columns,
            )
            session.execute(statement)
            return

        if dialect_name == "mysql":
            # MySQL 和 SQLite 的 upsert 语法不同，分支逻辑集中放在这里统一处理。
            statement = mysql_insert(model).values(rows)
            inserted = statement.inserted
            update_columns = {
                column.name: getattr(inserted, column.name)
                for column in model.__table__.columns
                if column.name not in {"id", "created_at", "updated_at", *unique_columns}
            }
            statement = statement.on_duplicate_key_update(**update_columns)
            session.execute(statement)
            return

        for row in rows:
            session.merge(model(**row))

    @staticmethod
    def _to_optional_float(value):
        if value is None or pd.isna(value):
            return None
        return float(value)

    @staticmethod
    def _to_optional_int(value):
        if value is None or pd.isna(value):
            return None
        return int(float(value))
