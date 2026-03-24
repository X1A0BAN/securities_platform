# 用途：同步交易日历数据到数据库。
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.collectors.trade_calendar_collector import TushareTradeCalendarCollector
from app.services.sync_service import SyncService
from app.utils.date_utils import parse_date


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="从 Tushare 同步交易日历。")
    parser.add_argument(
        "--years",
        type=int,
        default=3,
        help="同步的历史年数，默认 3 年。",
    )
    parser.add_argument(
        "--end-date",
        type=str,
        default=None,
        help="可选结束日期，支持 YYYY-MM-DD 或 YYYYMMDD。",
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
    trade_calendar_collector = (
        TushareTradeCalendarCollector(token=args.token) if args.token else None
    )
    service = SyncService(trade_calendar_collector=trade_calendar_collector)
    summary = service.sync_trade_calendar(
        years=args.years,
        end_date=parse_date(args.end_date) if args.end_date else None,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
