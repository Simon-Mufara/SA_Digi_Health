from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.engine import make_url
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import declarative_base, sessionmaker

from .config import settings

database_url = settings.database_url
parsed_url = make_url(database_url)
database_backend = parsed_url.get_backend_name()

if database_backend.startswith("sqlite") and parsed_url.database:
    sqlite_path = Path(parsed_url.database)
    if not sqlite_path.is_absolute():
        backend_root = Path(__file__).resolve().parents[2]
        resolved_sqlite_path = (backend_root / sqlite_path).resolve()
        database_url = str(parsed_url.set(database=str(resolved_sqlite_path)))

primary_connect_args: dict[str, int] = {}
if database_backend.startswith("postgresql"):
    # Fail fast when local Postgres is unavailable, then use SQLite fallback.
    primary_connect_args["connect_timeout"] = 3

engine = create_engine(database_url, pool_pre_ping=True, connect_args=primary_connect_args)

try:
    with engine.connect():
        pass
except OperationalError:
    sqlite_fallback_path = Path(__file__).resolve().parents[2] / "clinic_local.db"
    fallback_url = f"sqlite+pysqlite:///{sqlite_fallback_path}"
    print(
        "Warning: primary database unavailable. "
        f"Falling back to SQLite at {sqlite_fallback_path}."
    )
    engine = create_engine(
        fallback_url,
        pool_pre_ping=True,
        connect_args={"check_same_thread": False},
    )

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
