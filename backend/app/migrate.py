"""SQLite 轻量迁移：为已有库补充新列。"""

from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from .database import engine


def _column_exists(table: str, column: str) -> bool:
    insp = inspect(engine)
    if table not in insp.get_table_names():
        return False
    return column in {c["name"] for c in insp.get_columns(table)}


def run_migrations() -> None:
    alters = [
        ("members", "estimated_balance", "REAL DEFAULT 0"),
        ("members", "confirmed_balance", "REAL DEFAULT 0"),
        ("members", "withdrawable_balance", "REAL DEFAULT 0"),
        ("members", "pending_balance", "REAL DEFAULT 0"),
        ("taku_apps", "kuaishou_security_key", "VARCHAR(128) DEFAULT ''"),
        ("members", "device_model", "VARCHAR(128) DEFAULT ''"),
        ("members", "device_unique_id", "VARCHAR(128) DEFAULT ''"),
    ]
    with engine.connect() as conn:
        for table, col, typedef in alters:
            if not _column_exists(table, col):
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {typedef}"))
        conn.commit()


def ensure_configs(db: Session, defaults: dict) -> None:
    from .models import SystemConfig

    for key, value in defaults.items():
        cfg = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        if not cfg:
            db.add(SystemConfig(key=key, value=str(value)))
    db.commit()
