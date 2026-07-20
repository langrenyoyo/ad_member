from sqlalchemy.orm import Session

from ..models import SystemConfig

DEFAULT_RISK_CONFIG = {
    "ad_risk_enabled": "1",
    "daily_ad_limit": "50",
    "incentive_interval_seconds": "30",
    "min_withdraw": "10",
    "taku_publisher_key": "",
    "reward_share_rate": "0.88",
    "confirm_delay_days": "1",
    "gap_alert_rate": "0.08",
    "taku_wait_seconds": "5",
    "device_daily_limit": "30",
    "risk_block_score": "70",
    "ip_daily_limit": "100",
}


def get_config_map(db: Session) -> dict[str, str]:
    configs = db.query(SystemConfig).all()
    result = dict(DEFAULT_RISK_CONFIG)
    for c in configs:
        result[c.key] = c.value
    return result


def cfg_float(cfg: dict, key: str, default: float) -> float:
    try:
        return float(cfg.get(key, default))
    except (TypeError, ValueError):
        return default


def cfg_int(cfg: dict, key: str, default: int) -> int:
    try:
        return int(cfg.get(key, default))
    except (TypeError, ValueError):
        return default


def is_risk_enabled(cfg: dict) -> bool:
    return cfg.get("ad_risk_enabled", "1") == "1"
