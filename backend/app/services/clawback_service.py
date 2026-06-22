from datetime import date, datetime, timedelta

from sqlalchemy import and_, case, func
from sqlalchemy.orm import Session

from ..models import IncentiveTransaction, Member


def _parse_range(date_start: str, date_end: str) -> tuple[datetime, datetime]:
    start_d = date.fromisoformat(date_start) if date_start else date.today() - timedelta(days=30)
    end_d = date.fromisoformat(date_end) if date_end else date.today()
    start = datetime.combine(start_d, datetime.min.time())
    end = datetime.combine(end_d + timedelta(days=1), datetime.min.time())
    return start, end


def clawback_summary(db: Session, date_start: str = "", date_end: str = "") -> dict:
    start, end = _parse_range(date_start, date_end)
    base = db.query(IncentiveTransaction).filter(
        IncentiveTransaction.created_at >= start,
        IncentiveTransaction.created_at < end,
    )

    clawback_amt = base.filter(IncentiveTransaction.status == "clawback").with_entities(
        func.sum(IncentiveTransaction.user_reward)
    ).scalar() or 0
    clawback_cnt = base.filter(IncentiveTransaction.status == "clawback").count()

    rejected_amt = base.filter(IncentiveTransaction.status == "rejected").with_entities(
        func.sum(IncentiveTransaction.user_reward)
    ).scalar() or 0
    rejected_cnt = base.filter(IncentiveTransaction.status == "rejected").count()

    pending_lost_amt = base.filter(
        IncentiveTransaction.status == "pending",
        IncentiveTransaction.kuaishou_verified == True,
        IncentiveTransaction.taku_verified == False,
    ).with_entities(func.sum(IncentiveTransaction.user_reward)).scalar() or 0
    pending_lost_cnt = base.filter(
        IncentiveTransaction.status == "pending",
        IncentiveTransaction.kuaishou_verified == True,
        IncentiveTransaction.taku_verified == False,
    ).count()

    user_rows = clawback_users_query(db, start, end, min_amount=0.0)
    affected_users = len(user_rows)

    total_deduction = float(clawback_amt) + float(rejected_amt) + float(pending_lost_amt)

    return {
        "date_start": start.date().isoformat(),
        "date_end": (end - timedelta(days=1)).date().isoformat(),
        "affected_users": affected_users,
        "total_deduction": round(total_deduction, 4),
        "clawback_amount": float(clawback_amt),
        "clawback_count": clawback_cnt,
        "rejected_amount": float(rejected_amt),
        "rejected_count": rejected_cnt,
        "pending_lost_amount": float(pending_lost_amt),
        "pending_lost_count": pending_lost_cnt,
    }


def clawback_users_query(
    db: Session,
    start: datetime,
    end: datetime,
    uid: str = "",
    min_amount: float = 0.0,
) -> list[dict]:
    clawback_amt = func.sum(
        case(
            (IncentiveTransaction.status == "clawback", IncentiveTransaction.user_reward),
            else_=0.0,
        )
    )
    clawback_cnt = func.sum(
        case((IncentiveTransaction.status == "clawback", 1), else_=0)
    )
    rejected_amt = func.sum(
        case(
            (IncentiveTransaction.status == "rejected", IncentiveTransaction.user_reward),
            else_=0.0,
        )
    )
    rejected_cnt = func.sum(
        case((IncentiveTransaction.status == "rejected", 1), else_=0)
    )
    pending_lost_amt = func.sum(
        case(
            (
                and_(
                    IncentiveTransaction.status == "pending",
                    IncentiveTransaction.kuaishou_verified == True,
                    IncentiveTransaction.taku_verified == False,
                ),
                IncentiveTransaction.user_reward,
            ),
            else_=0.0,
        )
    )
    pending_lost_cnt = func.sum(
        case(
            (
                and_(
                    IncentiveTransaction.status == "pending",
                    IncentiveTransaction.kuaishou_verified == True,
                    IncentiveTransaction.taku_verified == False,
                ),
                1,
            ),
            else_=0,
        )
    )
    total_deduction = clawback_amt + rejected_amt + pending_lost_amt

    q = db.query(
        IncentiveTransaction.uid,
        clawback_amt.label("clawback_amount"),
        clawback_cnt.label("clawback_count"),
        rejected_amt.label("rejected_amount"),
        rejected_cnt.label("rejected_count"),
        pending_lost_amt.label("pending_lost_amount"),
        pending_lost_cnt.label("pending_lost_count"),
        total_deduction.label("total_deduction"),
        func.max(IncentiveTransaction.created_at).label("last_at"),
    ).filter(
        IncentiveTransaction.created_at >= start,
        IncentiveTransaction.created_at < end,
    )
    if uid:
        q = q.filter(IncentiveTransaction.uid.contains(uid))

    q = q.group_by(IncentiveTransaction.uid)
    if min_amount > 0:
        q = q.having(total_deduction > min_amount)
    rows = q.order_by(total_deduction.desc()).all()

    if not rows:
        return []

    members = {
        m.uid: m
        for m in db.query(Member).filter(Member.uid.in_([r.uid for r in rows])).all()
    }

    result = []
    for r in rows:
        m = members.get(r.uid)
        total = float(r.total_deduction or 0)
        estimated_part = total  # for rate display use member balances if needed
        result.append({
            "uid": r.uid,
            "nickname": m.nickname if m else "",
            "mobile": m.mobile if m else "",
            "agent_type": m.agent_type if m else 0,
            "status": m.status if m else 1,
            "is_black": m.is_black if m else False,
            "estimated_balance": m.estimated_balance if m else 0,
            "confirmed_balance": m.confirmed_balance if m else 0,
            "clawback_amount": float(r.clawback_amount or 0),
            "clawback_count": int(r.clawback_count or 0),
            "rejected_amount": float(r.rejected_amount or 0),
            "rejected_count": int(r.rejected_count or 0),
            "pending_lost_amount": float(r.pending_lost_amount or 0),
            "pending_lost_count": int(r.pending_lost_count or 0),
            "total_deduction": total,
            "deduction_rate": round(
                total / max(m.estimated_balance + total, 0.01), 4
            ) if m else 0,
            "last_at": r.last_at.isoformat() if r.last_at else "",
        })
    return result


def clawback_user_list(
    db: Session,
    page: int = 1,
    limit: int = 20,
    uid: str = "",
    date_start: str = "",
    date_end: str = "",
    min_amount: float = 0.01,
) -> tuple[list[dict], int]:
    start, end = _parse_range(date_start, date_end)
    all_rows = clawback_users_query(db, start, end, uid=uid, min_amount=min_amount)
    total = len(all_rows)
    start_idx = (page - 1) * limit
    return all_rows[start_idx:start_idx + limit], total


def clawback_user_detail(
    db: Session,
    uid: str,
    date_start: str = "",
    date_end: str = "",
    page: int = 1,
    limit: int = 20,
) -> tuple[list[dict], int]:
    start, end = _parse_range(date_start, date_end)
    q = db.query(IncentiveTransaction).filter(
        IncentiveTransaction.uid == uid,
        IncentiveTransaction.created_at >= start,
        IncentiveTransaction.created_at < end,
    )
    q = q.filter(
        (IncentiveTransaction.status.in_(["clawback", "rejected"]))
        | (
            (IncentiveTransaction.status == "pending")
            & (IncentiveTransaction.kuaishou_verified == True)
            & (IncentiveTransaction.taku_verified == False)
        )
    )
    total = q.count()
    items = q.order_by(IncentiveTransaction.id.desc()).offset((page - 1) * limit).limit(limit).all()

    def deduction_type(t: IncentiveTransaction) -> str:
        if t.status == "clawback":
            return "clawback"
        if t.status == "rejected":
            return "rejected"
        return "pending_lost"

    def deduction_reason(t: IncentiveTransaction) -> str:
        if t.status == "clawback":
            return t.remark or "平台核减扣回"
        if t.status == "rejected":
            return "风控拒绝"
        return "双回调未齐，视同核减"

    return [
        {
            "trans_id": t.trans_id,
            "user_reward": t.user_reward,
            "revenue": t.revenue,
            "status": t.status,
            "deduction_type": deduction_type(t),
            "reason": deduction_reason(t),
            "kuaishou_verified": t.kuaishou_verified,
            "taku_verified": t.taku_verified,
            "device_id": t.device_id,
            "ip": t.ip,
            "created_at": t.created_at.isoformat(),
        }
        for t in items
    ], total
