from datetime import datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import ContainmentLog, IncentiveTransaction, Member, RiskDecisionLog, WhiteList
from .config_service import cfg_int, get_config_map, is_risk_enabled


def _is_whitelisted(db: Session, uid: str) -> bool:
    return db.query(WhiteList).filter(WhiteList.uid == uid, WhiteList.status == 1).first() is not None


def _today_start() -> datetime:
    today = datetime.utcnow().date()
    return datetime.combine(today, datetime.min.time())


def evaluate_risk(
    db: Session,
    uid: str,
    device_id: str = "",
    ip: str = "",
    trans_id: str = "",
) -> tuple[bool, int, list[dict]]:
    cfg = get_config_map(db)
    if not is_risk_enabled(cfg) or _is_whitelisted(db, uid):
        return True, 0, []

    member = db.query(Member).filter(Member.uid == uid).first()
    if member and (member.is_black or member.status == 0):
        _log_decision(db, uid, trans_id, "账号冻结/拉黑", 100, 100, "block", "账号状态异常")
        return False, 100, [{"rule": "账号冻结/拉黑", "score": 100}]

    score = 0
    hits: list[dict] = []
    start = _today_start()

    daily_limit = cfg_int(cfg, "daily_ad_limit", 50)
    device_limit = cfg_int(cfg, "device_daily_limit", 30)
    ip_limit = cfg_int(cfg, "ip_daily_limit", 100)
    block_score = cfg_int(cfg, "risk_block_score", 70)

    uid_count = db.query(IncentiveTransaction).filter(
        IncentiveTransaction.uid == uid,
        IncentiveTransaction.created_at >= start,
        IncentiveTransaction.status != "rejected",
    ).count()
    if uid_count >= daily_limit:
        score += 40
        hits.append({"rule": "用户日激励超限", "score": 40, "detail": f"{uid_count}/{daily_limit}"})

    if device_id:
        dev_count = db.query(IncentiveTransaction).filter(
            IncentiveTransaction.device_id == device_id,
            IncentiveTransaction.created_at >= start,
            IncentiveTransaction.status != "rejected",
        ).count()
        if dev_count >= device_limit:
            score += 35
            hits.append({"rule": "设备日激励超限", "score": 35, "detail": f"{dev_count}/{device_limit}"})

    if ip:
        ip_count = db.query(IncentiveTransaction).filter(
            IncentiveTransaction.ip == ip,
            IncentiveTransaction.created_at >= start,
            IncentiveTransaction.status != "rejected",
        ).count()
        if ip_count >= ip_limit:
            score += 25
            hits.append({"rule": "IP日激励超限", "score": 25, "detail": f"{ip_count}/{ip_limit}"})

    passed = score < block_score
    action = "pass" if passed else "block"
    for h in hits:
        _log_decision(
            db,
            uid,
            trans_id,
            h["rule"],
            h["score"],
            score,
            action,
            h.get("detail", ""),
        )

    if not passed:
        db.add(ContainmentLog(uid=uid, reason=f"风控拦截 风险分{score}", action="block"))
    return passed, score, hits


def _log_decision(
    db: Session,
    uid: str,
    trans_id: str,
    rule: str,
    delta: int,
    total: int,
    action: str,
    detail: str,
) -> None:
    db.add(
        RiskDecisionLog(
            uid=uid,
            trans_id=trans_id,
            rule_name=rule,
            score_delta=delta,
            total_score=total,
            action=action,
            detail=detail,
        )
    )
