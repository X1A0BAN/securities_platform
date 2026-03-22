from __future__ import annotations

from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import get_settings


settings = get_settings()

connect_args = {}
if settings.database_url.startswith("sqlite"):
    connect_args["check_same_thread"] = False

engine = create_engine(
    settings.database_url,
    future=True,
    pool_pre_ping=True,
    connect_args=connect_args,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False, future=True)
Base = declarative_base()


@contextmanager
def session_scope():
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()


def init_db() -> None:
    # 这里集中导入模型，确保 create_all 之前 SQLAlchemy 已经完成表元数据注册。
    import app.models.adj_factor_model  # noqa: F401
    import app.models.daily_price_model  # noqa: F401
    import app.models.stock_model  # noqa: F401
    import app.models.trade_calendar_model  # noqa: F401

    Base.metadata.create_all(bind=engine)
