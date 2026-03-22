from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parents[1]
DEFAULT_SQLITE_PATH = BASE_DIR / "securities_platform.db"


def _read_float_env(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value == "":
        return default

    try:
        return float(raw_value)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be a float.") from exc


@dataclass(frozen=True)
class Settings:
    database_url: str
    tushare_token: str | None
    tushare_pause_seconds: float
    hs300_index_code: str


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings(
        database_url=os.getenv(
            "DATABASE_URL",
            f"sqlite:///{DEFAULT_SQLITE_PATH.as_posix()}",
        ),
        tushare_token=os.getenv("TUSHARE_TOKEN"),
        tushare_pause_seconds=_read_float_env("TUSHARE_PAUSE_SECONDS", 0.2),
        hs300_index_code=os.getenv("HS300_INDEX_CODE", "399300.SZ"),
    )
