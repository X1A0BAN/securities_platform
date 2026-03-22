from __future__ import annotations

import sys
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings
from app.db import init_db


def main() -> None:
    settings = get_settings()
    init_db()
    print(f"Database initialized: {settings.database_url}")


if __name__ == "__main__":
    main()
