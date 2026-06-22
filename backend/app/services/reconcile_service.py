from datetime import date, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from ..models import IncentiveTransaction, ReconcileDaily
from .config_service import cfg_float, get_config_map
from .incentive_service import process_daily_clawbacks, release_withdrawable_balances


def run_daily_reconcile(db: Session, target: date | None = None) -> ReconcileDaily:
    target = target or (date.today() - timedelta(days=1))
    process_daily_clawbacks(db, target)
    date_str = target.isoformat()
    start = datetime.combine(target, datetime.min.time())
    end = start + timedelta(days=1)

    estimated = db.query(func.sum(IncentiveTransaction.user_reward)).filter(
        IncentiveTransaction.created_at >= start,
        IncentiveTransaction.created_at < end,
        IncentiveTransaction.status.in_(["pending", "confirmed", "clawback"]),
    ).scalar() or 0

    confirmed = db.query(func.sum(IncentiveTransaction.user_reward)).filter(
        IncentiveTransaction.created_at >= start,
        IncentiveTransaction.created_at < end,
        IncentiveTransaction.status == "confirmed",
    ).scalar() or 0

    clawback = db.query(func.sum(IncentiveTransaction.user_reward)).filter(
        IncentiveTransaction.created_at >= start,
        IncentiveTransaction.created_at < end,
        IncentiveTransaction.status == "clawback",
    ).scalar() or 0

    tx_count = db.query(IncentiveTransaction).filter(
        IncentiveTransaction.created_at >= start,
        IncentiveTransaction.created_at < end,
    ).count()

    confirmed_count = db.query(IncentiveTransaction).filter(
        IncentiveTransaction.created_at >= start,
        IncentiveTransaction.created_at < end,
        IncentiveTransaction.status == "confirmed",
    ).count()

    kuaishou_revenue = db.query(func.sum(IncentiveTransaction.revenue)).filter(
        IncentiveTransaction.created_at >= start,
        IncentiveTransaction.created_at < end,
        IncentiveTransaction.kuaishou_verified == True,
    ).scalar() or 0

    taku_revenue = db.query(func.sum(IncentiveTransaction.revenue)).filter(
        IncentiveTransaction.created_at >= start,
        IncentiveTransaction.created_at < end,
        IncentiveTransaction.taku_verified == True,
    ).scalar() or 0

    gap_amount = float(estimated) - float(confirmed)
    gap_rate = (gap_amount / float(estimated)) if estimated else 0.0

    cfg = get_config_map(db)
    alert_rate = cfg_float(cfg, "gap_alert_rate", 0.08)
    status = "alert" if gap_rate > alert_rate else "done"

    row = db.query(ReconcileDaily).filter(ReconcileDaily.date == date_str).first()
    if not row:
        row = ReconcileDaily(date=date_str)
        db.add(row)

    row.estimated_revenue = float(estimated)
    row.confirmed_revenue = float(confirmed)
    row.taku_revenue = float(taku_revenue)
    row.kuaishou_revenue = float(kuaishou_revenue)
    row.gap_amount = float(gap_amount)
    row.gap_rate = round(gap_rate, 4)
    row.transaction_count = tx_count
    row.confirmed_count = confirmed_count
    row.clawback_amount = float(clawback)
    row.status = status
    row.updated_at = datetime.utcnow()

    release_withdrawable_balances(db)
    db.commit()
    return row
