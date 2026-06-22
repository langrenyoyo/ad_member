from datetime import date, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..auth import get_admin_id, ok
from ..database import get_db
from ..models import AdLog, IncentiveTransaction, Member

router = APIRouter()


@router.get("/index/index")
def index_overview(admin_id: int = Depends(get_admin_id), db: Session = Depends(get_db)):
    today = date.today()
    yesterday = today - timedelta(days=1)
    month_start = today.replace(day=1)

    total_revenue = db.query(func.sum(Member.total_revenue)).scalar() or 0
    today_revenue = db.query(func.sum(Member.today_revenue)).scalar() or 0
    estimated_balance = db.query(func.sum(Member.estimated_balance)).scalar() or 0
    confirmed_balance = db.query(func.sum(Member.confirmed_balance)).scalar() or 0
    withdrawable_balance = db.query(func.sum(Member.withdrawable_balance)).scalar() or 0
    pending_balance = db.query(func.sum(Member.pending_balance)).scalar() or 0
    member_count = db.query(Member).count()
    yesterday_active = db.query(Member).filter(
        Member.last_active >= datetime.combine(yesterday, datetime.min.time()),
        Member.last_active < datetime.combine(today, datetime.min.time()),
    ).count()
    today_active = db.query(Member).filter(
        Member.last_active >= datetime.combine(today, datetime.min.time())
    ).count()

    month_revenue = db.query(func.sum(AdLog.revenue)).filter(
        AdLog.created_at >= datetime.combine(month_start, datetime.min.time())
    ).scalar() or 0
    yesterday_revenue = db.query(func.sum(AdLog.revenue)).filter(
        AdLog.created_at >= datetime.combine(yesterday, datetime.min.time()),
        AdLog.created_at < datetime.combine(today, datetime.min.time()),
    ).scalar() or 0

    today_start = datetime.combine(today, datetime.min.time())
    today_tx_pending = db.query(IncentiveTransaction).filter(
        IncentiveTransaction.created_at >= today_start,
        IncentiveTransaction.status == "pending",
    ).count()
    today_tx_confirmed = db.query(IncentiveTransaction).filter(
        IncentiveTransaction.created_at >= today_start,
        IncentiveTransaction.status == "confirmed",
    ).count()

    return ok({
        "total_revenue": float(total_revenue),
        "prev_revenue": float(month_revenue),
        "month_revenue": float(month_revenue),
        "yesterday_revenue": float(yesterday_revenue),
        "today_revenue": float(today_revenue),
        "estimated_balance": float(estimated_balance),
        "confirmed_balance": float(confirmed_balance),
        "withdrawable_balance": float(withdrawable_balance),
        "pending_balance": float(pending_balance),
        "Member_count": member_count,
        "yesterday_active": yesterday_active,
        "today_active": today_active,
        "today_tx_pending": today_tx_pending,
        "today_tx_confirmed": today_tx_confirmed,
        "see": 1,
    })


@router.get("/index/member")
def index_member(time: str = "", admin_id: int = Depends(get_admin_id), db: Session = Depends(get_db)):
    target = date.fromisoformat(time) if time else date.today()
    start = datetime.combine(target, datetime.min.time())
    end = start + timedelta(days=1)
    members = db.query(Member).filter(
        Member.last_active >= start, Member.last_active < end
    ).all()
    return ok(list=[{
        "uid": m.uid,
        "nickname": m.nickname,
        "mobile": m.mobile,
        "today_revenue": m.today_revenue,
        "ad_count": m.ad_count,
        "estimated_balance": m.estimated_balance,
        "confirmed_balance": m.confirmed_balance,
        "withdrawable_balance": m.withdrawable_balance,
        "pending_balance": m.pending_balance,
    } for m in members], total=len(members))
