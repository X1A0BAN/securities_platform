from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.collectors.daily_price_collector import TushareDailyPriceCollector
from app.services.sync_service import SyncService
from app.utils.date_utils import parse_date


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Backfill HS300 daily prices from Tushare.")
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
    collector = TushareDailyPriceCollector(token=args.token) if args.token else None
    service = SyncService(collector=collector)
    end_date = parse_date(args.end_date) if args.end_date else None
    summary = service.backfill_hs300_daily_prices(years=args.years, end_date=end_date)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
