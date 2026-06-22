from datetime import date, datetime

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import ContainmentLog, DistributionLevel, IncentiveTransaction, Member, RiskDecisionLog


def member_stats(db: Session) -> dict:
    today = date.today()
    today_start = datetime.combine(today, datetime.min.time())

    total = db.query(Member).count()
    today_active = db.query(Member).filter(Member.last_active >= today_start).count()
    promoters = db.query(Member).filter(Member.agent_type > 0).count()
    frozen = db.query(Member).filter(Member.status == 0).count()
    black = db.query(Member).filter(Member.is_black == True).count()
    pending_total = db.query(func.sum(Member.pending_balance)).scalar() or 0
    withdrawable_total = db.query(func.sum(Member.withdrawable_balance)).scalar() or 0

    return {
        "total": total,
        "today_active": today_active,
        "promoters": promoters,
        "frozen": frozen,
        "black": black,
        "pending_total": float(pending_total),
        "withdrawable_total": float(withdrawable_total),
    }


def member_detail(db: Session, uid: str) -> dict | None:
    m = db.query(Member).filter(Member.uid == uid).first()
    if not m:
        return None

    level_name = ""
    if m.level_id:
        level = db.get(DistributionLevel, m.level_id)
        if level:
            level_name = level.name

    tx_pending = db.query(IncentiveTransaction).filter(
        IncentiveTransaction.uid == uid,
        IncentiveTransaction.status == "pending",
    ).count()
    tx_confirmed = db.query(IncentiveTransaction).filter(
        IncentiveTransaction.uid == uid,
        IncentiveTransaction.status == "confirmed",
    ).count()
    tx_clawback = db.query(IncentiveTransaction).filter(
        IncentiveTransaction.uid == uid,
        IncentiveTransaction.status == "clawback",
    ).count()
    clawback_amount = db.query(func.sum(IncentiveTransaction.user_reward)).filter(
        IncentiveTransaction.uid == uid,
        IncentiveTransaction.status == "clawback",
    ).scalar() or 0

    risk_blocks = db.query(ContainmentLog).filter(ContainmentLog.uid == uid).count()
    risk_decisions = db.query(RiskDecisionLog).filter(
        RiskDecisionLog.uid == uid,
        RiskDecisionLog.action == "block",
    ).count()

    return {
        "level_name": level_name,
        "tx_pending": tx_pending,
        "tx_confirmed": tx_confirmed,
        "tx_clawback": tx_clawback,
        "clawback_amount": float(clawback_amount),
        "risk_blocks": risk_blocks,
        "risk_decisions": risk_decisions,
    }
