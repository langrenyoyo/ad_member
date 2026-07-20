from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth import get_admin_id, ok
from ..database import get_db
from ..models import (
    CallbackLog,
    IncentiveTransaction,
    ReconcileDaily,
    RiskDecisionLog,
    SystemConfig,
)
from ..services.config_service import DEFAULT_RISK_CONFIG
from ..services.clawback_service import clawback_summary, clawback_user_detail, clawback_user_list
from ..services.reconcile_service import run_daily_reconcile

router = APIRouter()


@router.get("/risk/config")
def risk_config(admin_id: int = Depends(get_admin_id), db: Session = Depends(get_db)):
    configs = db.query(SystemConfig).all()
    data = dict(DEFAULT_RISK_CONFIG)
    for c in configs:
        data[c.key] = c.value
    return ok(data)


class RiskConfigBody(BaseModel):
    configs: dict


@router.post("/risk/config/save")
def risk_config_save(body: RiskConfigBody, admin_id: int = Depends(get_admin_id), db: Session = Depends(get_db)):
    for key, value in body.configs.items():
        cfg = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        if cfg:
            cfg.value = str(value)
        else:
            db.add(SystemConfig(key=key, value=str(value)))
    db.commit()
    return ok()


@router.get("/risk/transactions")
def risk_transactions(
    page: int = 1,
    limit: int = 20,
    uid: str = "",
    status: str = "",
    network_code: str = "",
    admin_id: int = Depends(get_admin_id),
    db: Session = Depends(get_db),
):
    q = db.query(IncentiveTransaction)
    if uid:
        q = q.filter(IncentiveTransaction.uid == uid)
    if status:
        q = q.filter(IncentiveTransaction.status == status)
    if network_code:
        q = q.filter(IncentiveTransaction.network_code == network_code)
    total = q.count()
    items = q.order_by(IncentiveTransaction.id.desc()).offset((page - 1) * limit).limit(limit).all()
    return ok(
        list=[_tx_item(t) for t in items],
        total=total,
    )


def _tx_item(t: IncentiveTransaction) -> dict:
    return {
        "id": t.id,
        "trans_id": t.trans_id,
        "uid": t.uid,
        "app_id": t.app_id,
        "placement_id": t.placement_id,
        "network_firm_id": t.network_firm_id,
        "network_code": t.network_code,
        "network_verified": t.network_verified,
        "network_at": t.network_at.isoformat() if t.network_at else "",
        "revenue": t.revenue,
        "user_reward": t.user_reward,
        "status": t.status,
        "kuaishou_verified": t.kuaishou_verified,
        "taku_verified": t.taku_verified,
        "kuaishou_at": t.kuaishou_at.isoformat() if t.kuaishou_at else "",
        "taku_at": t.taku_at.isoformat() if t.taku_at else "",
        "device_id": t.device_id,
        "ip": t.ip,
        "risk_score": t.risk_score,
        "risk_passed": t.risk_passed,
        "remark": t.remark,
        "created_at": t.created_at.isoformat(),
        "confirmed_at": t.confirmed_at.isoformat() if t.confirmed_at else "",
    }


@router.get("/risk/callback_logs")
def callback_logs(
    page: int = 1,
    limit: int = 20,
    source: str = "",
    admin_id: int = Depends(get_admin_id),
    db: Session = Depends(get_db),
):
    q = db.query(CallbackLog)
    if source:
        q = q.filter(CallbackLog.source == source)
    total = q.count()
    items = q.order_by(CallbackLog.id.desc()).offset((page - 1) * limit).limit(limit).all()
    return ok(
        list=[{
            "id": c.id,
            "source": c.source,
            "trans_id": c.trans_id,
            "sign_ok": c.sign_ok,
            "raw_body": c.raw_body[:500],
            "created_at": c.created_at.isoformat(),
        } for c in items],
        total=total,
    )


@router.get("/risk/decisions")
def risk_decisions(
    page: int = 1,
    limit: int = 20,
    uid: str = "",
    admin_id: int = Depends(get_admin_id),
    db: Session = Depends(get_db),
):
    q = db.query(RiskDecisionLog)
    if uid:
        q = q.filter(RiskDecisionLog.uid == uid)
    total = q.count()
    items = q.order_by(RiskDecisionLog.id.desc()).offset((page - 1) * limit).limit(limit).all()
    return ok(
        list=[{
            "id": d.id,
            "uid": d.uid,
            "trans_id": d.trans_id,
            "rule_name": d.rule_name,
            "score_delta": d.score_delta,
            "total_score": d.total_score,
            "action": d.action,
            "detail": d.detail,
            "created_at": d.created_at.isoformat(),
        } for d in items],
        total=total,
    )


@router.get("/risk/reconcile/daily")
def reconcile_daily_list(
    page: int = 1,
    limit: int = 20,
    admin_id: int = Depends(get_admin_id),
    db: Session = Depends(get_db),
):
    q = db.query(ReconcileDaily)
    total = q.count()
    items = q.order_by(ReconcileDaily.date.desc()).offset((page - 1) * limit).limit(limit).all()
    return ok(list=[_reconcile_item(r) for r in items], total=total)


def _reconcile_item(r: ReconcileDaily) -> dict:
    return {
        "id": r.id,
        "date": r.date,
        "estimated_revenue": r.estimated_revenue,
        "confirmed_revenue": r.confirmed_revenue,
        "taku_revenue": r.taku_revenue,
        "kuaishou_revenue": r.kuaishou_revenue,
        "gap_amount": r.gap_amount,
        "gap_rate": r.gap_rate,
        "transaction_count": r.transaction_count,
        "confirmed_count": r.confirmed_count,
        "clawback_amount": r.clawback_amount,
        "status": r.status,
        "updated_at": r.updated_at.isoformat(),
    }


class ReconcileRunBody(BaseModel):
    date: str = ""


@router.post("/risk/reconcile/run")
def reconcile_run(
    body: ReconcileRunBody,
    admin_id: int = Depends(get_admin_id),
    db: Session = Depends(get_db),
):
    target = date.fromisoformat(body.date) if body.date else None
    row = run_daily_reconcile(db, target)
    return ok(_reconcile_item(row))


@router.get("/risk/clawback/summary")
def clawback_summary_api(
    date_start: str = "",
    date_end: str = "",
    admin_id: int = Depends(get_admin_id),
    db: Session = Depends(get_db),
):
    return ok(clawback_summary(db, date_start, date_end))


@router.get("/risk/clawback/users")
def clawback_users_api(
    page: int = 1,
    limit: int = 20,
    uid: str = "",
    date_start: str = "",
    date_end: str = "",
    min_amount: float = 0.01,
    admin_id: int = Depends(get_admin_id),
    db: Session = Depends(get_db),
):
    items, total = clawback_user_list(
        db, page, limit, uid, date_start, date_end, min_amount
    )
    return ok(list=items, total=total)


@router.get("/risk/clawback/detail")
def clawback_detail_api(
    uid: str,
    page: int = 1,
    limit: int = 20,
    date_start: str = "",
    date_end: str = "",
    admin_id: int = Depends(get_admin_id),
    db: Session = Depends(get_db),
):
    items, total = clawback_user_detail(db, uid, date_start, date_end, page, limit)
    return ok(list=items, total=total)
