from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.sqlite import insert as sqlite_insert

from app.collectors.daily_price_collector import TushareDailyPriceCollector
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
        trade_calendar_collector: TushareTradeCalendarCollector | None = None,
    ) -> None:
        self.collector = collector or TushareDailyPriceCollector()
        self.trade_calendar_collector = trade_calendar_collector or TushareTradeCalendarCollector()

    def backfill_hs300_daily_prices(
        self,
        years: int = 3,
        end_date: date | None = None,
        start_date: date | None = None,
    ) -> dict[str, object]:
        effective_end_date = end_date or date.today()
        effective_start_date = start_date or years_ago(effective_end_date, years)

        constituents = self.collector.get_hs300_constituents(as_of_date=effective_end_date)
        if constituents.empty:
            raise RuntimeError("No HS300 constituent data returned from Tushare.")

        constituent_codes = constituents["con_code"].dropna().drop_duplicates().tolist()
        basics = self.collector.get_stock_basics(constituent_codes)

        logger.info(
            "Preparing to backfill %s HS300 constituents from %s to %s.",
            len(constituent_codes),
            effective_start_date,
            effective_end_date,
        )

        with session_scope() as session:
            stock_payloads = self._build_stock_payloads(constituents, basics)
            if stock_payloads:
                self._upsert_rows(session, Stock, stock_payloads, unique_columns=["ts_code"])

        summary: dict[str, object] = {
            "hs300_trade_date": str(parse_date(constituents["trade_date"].max())),
            "stock_count": len(constituent_codes),
            "stocks_processed": 0,
            "rows_written": 0,
            "start_date": str(effective_start_date),
            "end_date": str(effective_end_date),
        }

        for index, ts_code in enumerate(constituent_codes, start=1):
            logger.info("Fetching %s/%s %s", index, len(constituent_codes), ts_code)
            price_df = self.collector.fetch_daily_prices(
                ts_code=ts_code,
                start_date=effective_start_date,
                end_date=effective_end_date,
            )
            if price_df.empty:
                logger.warning("No daily price data returned for %s.", ts_code)
                continue

            price_payloads = self._build_daily_price_payloads(price_df)
            with session_scope() as session:
                self._upsert_rows(
                    session,
                    DailyPrice,
                    price_payloads,
                    unique_columns=["ts_code", "trade_date"],
                )

            summary["stocks_processed"] = int(summary["stocks_processed"]) + 1
            summary["rows_written"] = int(summary["rows_written"]) + len(price_payloads)

        logger.info("Backfill completed: %s", summary)
        return summary

    def backfill_hs300_adj_factors(
        self,
        years: int = 3,
        end_date: date | None = None,
        start_date: date | None = None,
    ) -> dict[str, object]:
        effective_end_date = end_date or date.today()
        effective_start_date = start_date or years_ago(effective_end_date, years)

        constituents = self.collector.get_hs300_constituents(as_of_date=effective_end_date)
        constituent_codes = constituents["con_code"].dropna().drop_duplicates().tolist()

        logger.info(
            "Preparing to backfill %s HS300 adj factors from %s to %s.",
            len(constituent_codes),
            effective_start_date,
            effective_end_date,
        )

        summary: dict[str, object] = {
            "hs300_trade_date": str(parse_date(constituents["trade_date"].max())),
            "stock_count": len(constituent_codes),
            "stocks_processed": 0,
            "rows_written": 0,
            "start_date": str(effective_start_date),
            "end_date": str(effective_end_date),
        }

        for index, ts_code in enumerate(constituent_codes, start=1):
            logger.info("Fetching adj factor %s/%s %s", index, len(constituent_codes), ts_code)
            adj_factor_df = self.collector.fetch_adj_factors(
                ts_code=ts_code,
                start_date=effective_start_date,
                end_date=effective_end_date,
            )
            if adj_factor_df.empty:
                logger.warning("No adj factor data returned for %s.", ts_code)
                continue

            adj_factor_payloads = self._build_adj_factor_payloads(adj_factor_df)
            with session_scope() as session:
                self._upsert_rows(
                    session,
                    AdjFactor,
                    adj_factor_payloads,
                    unique_columns=["ts_code", "trade_date"],
                )

            summary["stocks_processed"] = int(summary["stocks_processed"]) + 1
            summary["rows_written"] = int(summary["rows_written"]) + len(adj_factor_payloads)

        logger.info("Adj factor backfill completed: %s", summary)
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

            trade_calendar_payloads = self._build_trade_calendar_payloads(trade_calendar_df)
            with session_scope() as session:
                self._upsert_rows(
                    session,
                    TradeCalendar,
                    trade_calendar_payloads,
                    unique_columns=["trade_date", "exchange"],
                )

            summary["rows_written"] = int(summary["rows_written"]) + len(trade_calendar_payloads)
            cast_exchanges = summary["exchanges"]
            if isinstance(cast_exchanges, list):
                cast_exchanges.append(exchange)

        logger.info("Trade calendar sync completed: %s", summary)
        return summary

    def sync_recent_hs300_daily_prices(
        self,
        lookback_days: int = 10,
        end_date: date | None = None,
    ) -> dict[str, object]:
        effective_end_date = end_date or date.today()
        start_date = effective_end_date - timedelta(days=lookback_days)
        return self.backfill_hs300_daily_prices(
            years=0,
            end_date=effective_end_date,
            start_date=start_date,
        )

    def _build_stock_payloads(self, constituents, basics) -> list[dict[str, object]]:
        basic_lookup = {}
        if basics is not None and not basics.empty:
            basic_lookup = basics.set_index("ts_code").to_dict("index")

        trade_date = parse_date(constituents["trade_date"].max())
        payloads: list[dict[str, object]] = []
        for row in constituents.itertuples(index=False):
            basic_row = basic_lookup.get(row.con_code, {})
            payloads.append(
                {
                    "ts_code": row.con_code,
                    "symbol": basic_row.get("symbol") or row.con_code.split(".")[0],
                    "name": basic_row.get("name") or row.con_code,
                    "industry": basic_row.get("industry"),
                    "market": basic_row.get("market"),
                    "exchange": row.con_code.split(".")[-1],
                    "list_date": (
                        parse_date(str(basic_row["list_date"]))
                        if pd.notna(basic_row.get("list_date"))
                        else None
                    ),
                    "delist_date": None,
                    "is_active": True,
                }
            )
        return payloads

    def _build_daily_price_payloads(self, price_df) -> list[dict[str, object]]:
        payloads: list[dict[str, object]] = []
        for row in price_df.itertuples(index=False):
            payloads.append(
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
            )
        return payloads

    def _build_adj_factor_payloads(self, adj_factor_df) -> list[dict[str, object]]:
        payloads: list[dict[str, object]] = []
        for row in adj_factor_df.itertuples(index=False):
            payloads.append(
                {
                    "ts_code": row.ts_code,
                    "trade_date": parse_date(row.trade_date),
                    "adj_factor": self._to_optional_float(row.adj_factor),
                }
            )
        return payloads

    def _build_trade_calendar_payloads(self, trade_calendar_df) -> list[dict[str, object]]:
        payloads: list[dict[str, object]] = []
        for row in trade_calendar_df.itertuples(index=False):
            payloads.append(
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
            )
        return payloads

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
