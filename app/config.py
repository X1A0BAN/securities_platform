from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache


def _read_float_env(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value == "":
        return default

    try:
        return float(raw_value)
    except ValueError as exc:
        raise ValueError(f"环境变量 {name} 必须是浮点数。") from exc


@dataclass(frozen=True)
class Settings:
    database_url: str
    tushare_token: str | None
    tushare_pause_seconds: float


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError(
            "缺少 DATABASE_URL。请将它设置为统一使用的 MySQL 数据库，"
            "例如：mysql+pymysql://root:123456@127.0.0.1:3306/securities_data?charset=utf8mb4"
        )

    return Settings(
        database_url=database_url,
        tushare_token=os.getenv("TUSHARE_TOKEN"),
        tushare_pause_seconds=_read_float_env("TUSHARE_PAUSE_SECONDS", 0.2),
    )
