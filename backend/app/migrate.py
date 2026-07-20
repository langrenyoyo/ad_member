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
        ("taku_apps", "tencent_security_key", "VARCHAR(128) DEFAULT ''"),
        ("taku_apps", "tencent_sign_method", "VARCHAR(32) DEFAULT 'hmac_sha256'"),
        ("taku_apps", "baidu_security_key", "VARCHAR(128) DEFAULT ''"),
        ("taku_apps", "baidu_sign_method", "VARCHAR(32) DEFAULT 'md5_secret_colon_transid'"),
        ("incentive_transactions", "network_code", "VARCHAR(16) DEFAULT 'kuaishou'"),
        ("incentive_transactions", "network_verified", "BOOLEAN DEFAULT 0"),
        ("incentive_transactions", "network_at", "DATETIME"),
        ("members", "device_model", "VARCHAR(128) DEFAULT ''"),
        ("members", "device_unique_id", "VARCHAR(128) DEFAULT ''"),
    ]
    with engine.connect() as conn:
        for table, col, typedef in alters:
            if not _column_exists(table, col):
                conn.execute(text(f"ALTER TABLE {table} ADD COLUMN {col} {typedef}"))
        conn.commit()

        if _column_exists("incentive_transactions", "network_verified"):
            conn.execute(text(
                "UPDATE incentive_transactions SET network_verified = kuaishou_verified, "
                "network_code = 'kuaishou', network_at = kuaishou_at "
                "WHERE kuaishou_verified = 1 AND network_verified = 0"
            ))
            conn.commit()

    _remove_team_leader_role()


def _remove_team_leader_role() -> None:
    """移除团长角色：存量用户降为代理，删除团长等级。"""
    insp = inspect(engine)
    if "members" not in insp.get_table_names():
        return
    with engine.connect() as conn:
        conn.execute(
            text(
                "UPDATE members SET agent_type = 1, level_id = 2 "
                "WHERE agent_type = 2"
            )
        )
        conn.execute(
            text(
                "UPDATE members SET level_id = 2 "
                "WHERE level_id = 3"
            )
        )
        if "distribution_levels" in insp.get_table_names():
            conn.execute(text("DELETE FROM distribution_levels WHERE name = '团长'"))
            conn.execute(text("DELETE FROM distribution_levels WHERE id = 3"))
        conn.commit()


def ensure_configs(db: Session, defaults: dict) -> None:
    from .models import SystemConfig

    for key, value in defaults.items():
        cfg = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        if not cfg:
            db.add(SystemConfig(key=key, value=str(value)))
    db.commit()
