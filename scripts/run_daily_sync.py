# 用途：执行主板股票的每日增量同步流程。
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.collectors.daily_price_collector import TushareDailyPriceCollector
from app.collectors.stock_basic_collector import TushareStockBasicCollector
from app.collectors.trade_calendar_collector import TushareTradeCalendarCollector
from app.services.sync_service import SyncService
from app.utils.date_utils import parse_date


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="执行沪深主板每日增量同步。"
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default=None,
        help="可选结束日期，支持 YYYY-MM-DD 或 YYYYMMDD。",
    )
    parser.add_argument(
        "--years",
        type=int,
        default=3,
        help="主板股票池回看年数，默认 3 年。",
    )
    parser.add_argument(
        "--calendar-lookback-days",
        type=int,
        default=30,
        help="交易日历向前刷新的自然日天数，默认 30 天。",
    )
    parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="可选 Tushare Token；不传时回退到 TUSHARE_TOKEN 环境变量。",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    end_date = parse_date(args.end_date) if args.end_date else None
    daily_price_collector = TushareDailyPriceCollector(token=args.token) if args.token else None
    stock_basic_collector = TushareStockBasicCollector(token=args.token) if args.token else None
    trade_calendar_collector = TushareTradeCalendarCollector(token=args.token) if args.token else None
    service = SyncService(
        collector=daily_price_collector,
        stock_basic_collector=stock_basic_collector,
        trade_calendar_collector=trade_calendar_collector,
    )

    summary = service.run_main_board_daily_sync(
        end_date=end_date,
        years=args.years,
        calendar_lookback_days=args.calendar_lookback_days,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
