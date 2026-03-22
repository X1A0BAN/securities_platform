from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.collectors.stock_basic_collector import TushareStockBasicCollector
from app.services.sync_service import SyncService
from app.utils.date_utils import parse_date


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="从 Tushare 同步沪深主板股票基础信息。")
    parser.add_argument("--years", type=int, default=3, help="用于股票池过滤的回看年数，默认 3 年。")
    parser.add_argument("--end-date", type=str, default=None, help="可选结束日期，支持 YYYY-MM-DD 或 YYYYMMDD。")
    parser.add_argument("--token", type=str, default=None, help="可选 Tushare Token；不传时回退到 TUSHARE_TOKEN 环境变量。")
    return parser


def main() -> None:
    args = build_parser().parse_args()
    stock_basic_collector = TushareStockBasicCollector(token=args.token) if args.token else None
    service = SyncService(stock_basic_collector=stock_basic_collector)
    summary = service.sync_main_board_stock_basics(
        years=args.years,
        end_date=parse_date(args.end_date) if args.end_date else None,
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
