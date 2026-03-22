from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.collectors.daily_price_collector import TushareDailyPriceCollector
from app.collectors.trade_calendar_collector import TushareTradeCalendarCollector
from app.services.sync_service import SyncService
from app.utils.date_utils import parse_date


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Sync trade calendar from Tushare.")
    parser.add_argument(
        "--years",
        type=int,
        default=3,
        help="How many years of history to import. Defaults to 3.",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default=None,
        help="Optional end date in YYYY-MM-DD or YYYYMMDD format.",
    )
    parser.add_argument(
        "--token",
        type=str,
        default=None,
        help="Optional Tushare token. Falls back to TUSHARE_TOKEN env var.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    daily_price_collector = TushareDailyPriceCollector(token=args.token) if args.token else None
    trade_calendar_collector = (
        TushareTradeCalendarCollector(token=args.token) if args.token else None
    )
    service = SyncService(
        collector=daily_price_collector,
        trade_calendar_collector=trade_calendar_collector,
    )
    summary = service.sync_trade_calendar(
        years=args.years,
        end_date=parse_date(args.end_date) if args.end_date else None,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
