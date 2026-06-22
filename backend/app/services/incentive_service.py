import hashlib
import json
from datetime import date, datetime, timedelta

from sqlalchemy.orm import Session

from ..models import AdLog, CallbackLog, IncentiveTransaction, Member
from .config_service import cfg_float, cfg_int, get_config_map
from .device_service import bind_member_device_from_params
from .risk_service import evaluate_risk


def verify_kuaishou_sign(app_security_key: str, trans_id: str, sign: str) -> bool:
    if not app_security_key or not trans_id or not sign:
        return False
    expected = hashlib.md5(f"{app_security_key}:{trans_id}".encode()).hexdigest()
    return expected.lower() == sign.lower()


def calc_user_reward(db: Session, revenue: float, member: Member | None) -> float:
    cfg = get_config_map(db)
    share = cfg_float(cfg, "reward_share_rate", 0.88)
    level_rate = 1.0
    if member and member.level_id:
        from ..models import DistributionLevel

        level = db.get(DistributionLevel, member.level_id)
        if level:
            level_rate = level.rate
    return round(revenue * share * level_rate, 4)


def _get_or_create_member(db: Session, uid: str) -> Member:
    member = db.query(Member).filter(Member.uid == uid).first()
    if not member:
        member = Member(uid=uid, nickname=f"用户{uid}")
        db.add(member)
        db.flush()
    return member


def _apply_pending(member: Member, amount: float) -> None:
    member.pending_balance = round(member.pending_balance + amount, 4)
    member.estimated_balance = round(member.estimated_balance + amount, 4)
    member.today_revenue = round(member.today_revenue + amount, 4)
    member.total_revenue = round(member.total_revenue + amount, 4)
    member.ad_count += 1
    member.last_active = datetime.utcnow()


def _move_pending_to_confirmed(member: Member, amount: float) -> None:
    member.pending_balance = round(max(0, member.pending_balance - amount), 4)
    member.confirmed_balance = round(member.confirmed_balance + amount, 4)


def _apply_clawback(member: Member, amount: float) -> None:
    member.pending_balance = round(max(0, member.pending_balance - amount), 4)
    member.estimated_balance = round(max(0, member.estimated_balance - amount), 4)
    member.total_revenue = round(max(0, member.total_revenue - amount), 4)
    member.today_revenue = round(max(0, member.today_revenue - amount), 4)


def try_confirm_transaction(db: Session, tx: IncentiveTransaction) -> bool:
    if tx.status != "pending":
        return False
    if not tx.kuaishou_verified or not tx.taku_verified or not tx.risk_passed:
        return False

    member = db.query(Member).filter(Member.uid == tx.uid).first()
    if not member:
        return False

    tx.status = "confirmed"
    tx.confirmed_at = datetime.utcnow()
    _move_pending_to_confirmed(member, tx.user_reward)

    cfg = get_config_map(db)
    delay_days = cfg_int(cfg, "confirm_delay_days", 1)
    if delay_days <= 0:
        member.withdrawable_balance = round(member.withdrawable_balance + tx.user_reward, 4)
    return True


def process_kuaishou_callback(
    db: Session,
    params: dict,
    app_security_key: str,
    raw_body: str = "",
) -> dict:
    trans_id = str(params.get("transId") or params.get("trans_id") or "")
    uid = str(params.get("userId") or params.get("uid") or params.get("user_id") or "")
    sign = str(params.get("sign") or "")
    app_id = str(params.get("appId") or params.get("app_id") or "")
    placement_id = str(params.get("placementId") or params.get("placement_id") or "")
    device_id = str(params.get("deviceId") or params.get("device_id") or "")
    ip = str(params.get("ip") or "")
    revenue = float(params.get("revenue") or params.get("amount") or 0)

    sign_ok = verify_kuaishou_sign(app_security_key, trans_id, sign)
    db.add(
        CallbackLog(
            source="kuaishou",
            trans_id=trans_id,
            sign_ok=sign_ok,
            raw_body=raw_body or json.dumps(params, ensure_ascii=False),
        )
    )

    if not sign_ok:
        return {"ok": False, "reason": "sign_invalid"}

    bind_member_device_from_params(db, uid, params, "kuaishou")

    existing = db.query(IncentiveTransaction).filter(IncentiveTransaction.trans_id == trans_id).first()
    if existing and existing.kuaishou_verified:
        return {"ok": True, "duplicate": True, "trans_id": trans_id}

    passed, risk_score, _ = evaluate_risk(db, uid, device_id, ip, trans_id)
    member = _get_or_create_member(db, uid)
    user_reward = calc_user_reward(db, revenue, member)

    if existing:
        tx = existing
        tx.kuaishou_verified = True
        tx.kuaishou_at = datetime.utcnow()
        tx.revenue = revenue or tx.revenue
        tx.user_reward = user_reward or tx.user_reward
        tx.risk_score = risk_score
        tx.risk_passed = passed
    else:
        tx = IncentiveTransaction(
            trans_id=trans_id,
            uid=uid,
            app_id=app_id,
            placement_id=placement_id,
            revenue=revenue,
            user_reward=user_reward,
            status="rejected" if not passed else "pending",
            kuaishou_verified=True,
            kuaishou_at=datetime.utcnow(),
            device_id=device_id,
            ip=ip,
            risk_score=risk_score,
            risk_passed=passed,
        )
        db.add(tx)
        db.flush()

    if passed and tx.status == "pending":
        _apply_pending(member, tx.user_reward)
        db.add(
            AdLog(
                uid=uid,
                app_name=app_id,
                placement=placement_id or "激励视频",
                revenue=tx.user_reward,
                action="reward_pending",
            )
        )

    try_confirm_transaction(db, tx)
    db.commit()
    return {
        "ok": True,
        "trans_id": trans_id,
        "status": tx.status,
        "user_reward": tx.user_reward,
        "ui_reward": tx.user_reward if passed else 0,
    }


def process_taku_callback(db: Session, params: dict, raw_body: str = "") -> dict:
    trans_id = str(
        params.get("trans_id")
        or params.get("transId")
        or params.get("third_trans_id")
        or params.get("extra")
        or ""
    )
    uid = str(params.get("user_id") or params.get("uid") or params.get("userId") or "")
    app_id = str(params.get("app_id") or params.get("appId") or "")
    placement_id = str(params.get("placement_id") or params.get("placementId") or "")
    network_firm_id = int(params.get("network_firm_id") or params.get("networkFirmId") or 28)
    revenue = float(params.get("revenue") or params.get("ecpm") or 0)

    if uid:
        bind_member_device_from_params(db, uid, params, "taku")

    db.add(
        CallbackLog(
            source="taku",
            trans_id=trans_id,
            sign_ok=True,
            raw_body=raw_body or json.dumps(params, ensure_ascii=False),
        )
    )

    tx = None
    if trans_id:
        tx = db.query(IncentiveTransaction).filter(IncentiveTransaction.trans_id == trans_id).first()

    if not tx and uid:
        tx = (
            db.query(IncentiveTransaction)
            .filter(
                IncentiveTransaction.uid == uid,
                IncentiveTransaction.status == "pending",
                IncentiveTransaction.taku_verified == False,
            )
            .order_by(IncentiveTransaction.id.desc())
            .first()
        )

    if not tx:
        member = _get_or_create_member(db, uid)
        user_reward = calc_user_reward(db, revenue, member)
        trans_id = trans_id or f"taku_{uid}_{int(datetime.utcnow().timestamp() * 1000)}"
        tx = IncentiveTransaction(
            trans_id=trans_id,
            uid=uid,
            app_id=app_id,
            placement_id=placement_id,
            network_firm_id=network_firm_id,
            revenue=revenue,
            user_reward=user_reward,
            status="pending",
            taku_verified=True,
            taku_at=datetime.utcnow(),
        )
        db.add(tx)
    else:
        if tx.taku_verified:
            db.commit()
            return {"ok": True, "duplicate": True, "trans_id": tx.trans_id}
        tx.taku_verified = True
        tx.taku_at = datetime.utcnow()
        if app_id:
            tx.app_id = app_id
        if placement_id:
            tx.placement_id = placement_id
        tx.network_firm_id = network_firm_id

    try_confirm_transaction(db, tx)
    db.commit()
    return {"ok": True, "trans_id": tx.trans_id, "status": tx.status}


def mark_transaction_clawback(db: Session, tx: IncentiveTransaction, reason: str) -> bool:
    """将事务标记为核减扣回，并同步扣减用户余额。"""
    if tx.status == "clawback":
        return False
    member = db.query(Member).filter(Member.uid == tx.uid).first()
    if tx.status == "pending" and member:
        _apply_clawback(member, tx.user_reward)
    elif tx.status == "confirmed" and member:
        member.confirmed_balance = round(max(0, member.confirmed_balance - tx.user_reward), 4)
        member.estimated_balance = round(max(0, member.estimated_balance - tx.user_reward), 4)
        member.total_revenue = round(max(0, member.total_revenue - tx.user_reward), 4)
        remark = tx.remark or ""
        if "[withdrawable]" in remark:
            member.withdrawable_balance = round(
                max(0, member.withdrawable_balance - tx.user_reward), 4
            )
    tx.status = "clawback"
    tx.remark = reason
    return True


def process_daily_clawbacks(db: Session, target: date) -> int:
    """对账日将快手已过、Taku 未过的 pending 事务核减为 clawback。"""
    from datetime import date as date_type

    if not isinstance(target, date_type):
        target = date_type.fromisoformat(str(target))
    start = datetime.combine(target, datetime.min.time())
    end = start + timedelta(days=1)
    stale = db.query(IncentiveTransaction).filter(
        IncentiveTransaction.status == "pending",
        IncentiveTransaction.created_at >= start,
        IncentiveTransaction.created_at < end,
        IncentiveTransaction.kuaishou_verified == True,
        IncentiveTransaction.taku_verified == False,
    ).all()
    count = 0
    for tx in stale:
        if mark_transaction_clawback(db, tx, "对账核减：Taku辅验未通过"):
            count += 1
    return count


def release_withdrawable_balances(db: Session) -> int:
    """T+N 将已确认余额转入可提现。"""
    cfg = get_config_map(db)
    delay_days = cfg_int(cfg, "confirm_delay_days", 1)
    if delay_days <= 0:
        return 0

    cutoff = datetime.utcnow() - timedelta(days=delay_days)
    txs = (
        db.query(IncentiveTransaction)
        .filter(
            IncentiveTransaction.status == "confirmed",
            IncentiveTransaction.confirmed_at <= cutoff,
        )
        .all()
    )
    count = 0
    for tx in txs:
        remark = tx.remark or ""
        if "[withdrawable]" in remark:
            continue
        member = db.query(Member).filter(Member.uid == tx.uid).first()
        if member:
            member.withdrawable_balance = round(member.withdrawable_balance + tx.user_reward, 4)
            tx.remark = (remark + "[withdrawable]").strip()
            count += 1
    db.commit()
    return count
