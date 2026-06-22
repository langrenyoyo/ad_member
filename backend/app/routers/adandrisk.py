from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..auth import get_admin_id, ok
from ..database import get_db
from ..models import AdLog, ContainmentLog, Member

router = APIRouter()


@router.get("/adandrisk/dailyreport")
def daily_report(
    date_str: str = "",
    admin_id: int = Depends(get_admin_id),
    db: Session = Depends(get_db),
):
    target = date.fromisoformat(date_str) if date_str else date.today()
    start = datetime.combine(target, datetime.min.time())
    end = start + timedelta(days=1)
    revenue = db.query(func.sum(AdLog.revenue)).filter(
        AdLog.created_at >= start, AdLog.created_at < end
    ).scalar() or 0
    count = db.query(AdLog).filter(AdLog.created_at >= start, AdLog.created_at < end).count()
    users = db.query(AdLog.uid).filter(AdLog.created_at >= start, AdLog.created_at < end).distinct().count()
    return ok({
        "date": target.isoformat(),
        "total_revenue": float(revenue),
        "ad_count": count,
        "active_users": users,
        "risk_blocked": db.query(ContainmentLog).filter(
            ContainmentLog.created_at >= start, ContainmentLog.created_at < end
        ).count(),
    })


@router.get("/adandrisk/adver_log")
def adver_log(
    page: int = 1,
    limit: int = 20,
    uid: str = "",
    admin_id: int = Depends(get_admin_id),
    db: Session = Depends(get_db),
):
    q = db.query(AdLog)
    if uid:
        q = q.filter(AdLog.uid == uid)
    total = q.count()
    items = q.order_by(AdLog.id.desc()).offset((page - 1) * limit).limit(limit).all()
    return ok(list=[{
        "id": a.id,
        "uid": a.uid,
        "app_name": a.app_name,
        "placement": a.placement,
        "revenue": a.revenue,
        "action": a.action,
        "created_at": a.created_at.isoformat(),
    } for a in items], total=total)


@router.get("/adandrisk/containment_log")
def containment_log(
    page: int = 1,
    limit: int = 20,
    admin_id: int = Depends(get_admin_id),
    db: Session = Depends(get_db),
):
    q = db.query(ContainmentLog)
    total = q.count()
    items = q.order_by(ContainmentLog.id.desc()).offset((page - 1) * limit).limit(limit).all()
    return ok(list=[{
        "id": c.id,
        "uid": c.uid,
        "reason": c.reason,
        "action": c.action,
        "created_at": c.created_at.isoformat(),
    } for c in items], total=total)
