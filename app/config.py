from __future__ import annotations

import os
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DOTENV_PATH = PROJECT_ROOT / ".env"


def _load_project_dotenv() -> None:
    if not DOTENV_PATH.exists():
        return

    for raw_line in DOTENV_PATH.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#"):
            continue

        if line.startswith("export "):
            line = line[len("export ") :].strip()

        if "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip()
        if not key:
            continue

        if len(value) >= 2 and value[0] == value[-1] and value[0] in {'"', "'"}:
            value = value[1:-1]

        # System environment variables still override .env values.
        os.environ.setdefault(key, value)


def _read_float_env(name: str, default: float) -> float:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value == "":
        return default

    try:
        return float(raw_value)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be a float.") from exc


def _read_int_env(name: str, default: int) -> int:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value == "":
        return default

    try:
        return int(raw_value)
    except ValueError as exc:
        raise ValueError(f"Environment variable {name} must be an integer.") from exc


def _read_bool_env(name: str, default: bool) -> bool:
    raw_value = os.getenv(name)
    if raw_value is None or raw_value == "":
        return default

    normalized = raw_value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False

    raise ValueError(f"Environment variable {name} must be a boolean.")


@dataclass(frozen=True)
class Settings:
    database_url: str
    tushare_token: str | None
    tushare_pause_seconds: float
    query_cache_enabled: bool
    query_cache_ttl_seconds: int
    query_cache_maxsize: int


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    _load_project_dotenv()
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        raise ValueError(
            "Missing DATABASE_URL. Example: "
            "mysql+pymysql://root:123456@127.0.0.1:3306/securities_data?charset=utf8mb4"
        )

    return Settings(
        database_url=database_url,
        tushare_token=os.getenv("TUSHARE_TOKEN"),
        tushare_pause_seconds=_read_float_env("TUSHARE_PAUSE_SECONDS", 0.2),
        query_cache_enabled=_read_bool_env("QUERY_CACHE_ENABLED", True),
        query_cache_ttl_seconds=_read_int_env("QUERY_CACHE_TTL_SECONDS", 300),
        query_cache_maxsize=_read_int_env("QUERY_CACHE_MAXSIZE", 512),
    )
