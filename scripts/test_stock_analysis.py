# 用途：调用股票分析服务执行基础查询，方便本地验证查询链路是否可用。
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.services.stock_analysis_service import StockAnalysisService
from app.utils.date_utils import parse_date


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="调用股票分析服务做基础查询测试。")
    parser.add_argument(
        "action",
        choices=["recent-prices", "top-gainers"],
        help="要执行的测试查询。",
    )
    parser.add_argument(
        "--ts-code",
        type=str,
        default=None,
        help="股票代码，例如 600000.SH。",
    )
    parser.add_argument(
        "--days",
        type=int,
        default=60,
        help="最近行情天数，默认 60。",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=50,
        help="榜单返回数量，默认 50。",
    )
    parser.add_argument(
        "--trade-date",
        type=str,
        default=None,
        help="可选交易日，支持 YYYY-MM-DD 或 YYYYMMDD。",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    service = StockAnalysisService()

    if args.action == "recent-prices":
        if not args.ts_code:
            raise SystemExit("recent-prices 模式必须传 --ts-code。")
        result = service.get_recent_prices(ts_code=args.ts_code, days=args.days)
    else:
        trade_date = parse_date(args.trade_date) if args.trade_date else None
        result = service.get_top_gainers(limit=args.limit, trade_date=trade_date)

    print(json.dumps(result, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
