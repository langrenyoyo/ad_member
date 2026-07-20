import hashlib
import hmac
import os
import time
from datetime import datetime
from threading import Lock
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, Query, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth import fail, ok
from ..database import get_db
from ..models import AdLog, IncentiveTransaction, Member, MemberDevice, TakuApp
from ..services.config_service import cfg_int, get_config_map
from ..services.device_service import bind_member_device
from ..services.risk_service import evaluate_risk

_USED_NONCES: dict[str, int] = {}
_NONCE_LOCK = Lock()

PUBLIC_CONFIG_KEYS = (
    "ad_risk_enabled",
    "daily_ad_limit",
    "incentive_interval_seconds",
    "min_withdraw",
    "reward_share_rate",
    "confirm_delay_days",
    "taku_wait_seconds",
    "device_daily_limit",
    "ip_daily_limit",
)


class AppAuthError(Exception):
    def __init__(self, msg: str, code: int = 401, status_code: int = 401):
        self.msg = msg
        self.code = code
        self.status_code = status_code


def _env_or_config(env_key: str, cfg: dict, cfg_key: str, default: str = "") -> str:
    return os.getenv(env_key) or str(cfg.get(cfg_key, default))


def _app_auth_config(db: Session) -> dict:
    cfg = get_config_map(db)
    window_raw = _env_or_config(
        "APP_API_TIME_WINDOW_SECONDS",
        cfg,
        "app_api_time_window_seconds",
        "300",
    )
    return {
        "enabled": _env_or_config("APP_API_AUTH_ENABLED", cfg, "app_api_auth_enabled", "1") == "1",
        "key": _env_or_config("APP_API_KEY", cfg, "app_api_key", "ad_member_app"),
        "secret": _env_or_config("APP_API_SECRET", cfg, "app_api_secret", ""),
        "window_seconds": cfg_int({"value": window_raw}, "value", 300),
    }


def _normalized_query(request: Request) -> str:
    pairs = sorted((key, value) for key, value in request.query_params.multi_items())
    return urlencode(pairs)


def _remember_nonce(app_key: str, nonce: str, now: int, window_seconds: int) -> None:
    nonce_key = f"{app_key}:{nonce}"
    with _NONCE_LOCK:
        expired = [key for key, expires_at in _USED_NONCES.items() if expires_at <= now]
        for key in expired:
            _USED_NONCES.pop(key, None)
        if nonce_key in _USED_NONCES:
            raise AppAuthError("app_nonce_replayed")
        _USED_NONCES[nonce_key] = now + window_seconds


async def verify_app_signature(request: Request, db: Session = Depends(get_db)) -> None:
    auth_cfg = _app_auth_config(db)
    if not auth_cfg["enabled"]:
        return

    app_key = (request.headers.get("x-app-key") or "").strip()
    timestamp = (request.headers.get("x-app-timestamp") or "").strip()
    nonce = (request.headers.get("x-app-nonce") or "").strip()
    signature = (request.headers.get("x-app-signature") or "").strip().lower()
    if not app_key or not timestamp or not nonce or not signature:
        raise AppAuthError("app_signature_headers_required")
    if app_key != auth_cfg["key"]:
        raise AppAuthError("app_key_invalid")
    if not auth_cfg["secret"]:
        raise AppAuthError("app_api_secret_not_configured", 500, 500)

    try:
        request_ts = int(timestamp)
    except ValueError as exc:
        raise AppAuthError("app_timestamp_invalid") from exc

    now = int(time.time())
    window_seconds = max(1, int(auth_cfg["window_seconds"]))
    if abs(now - request_ts) > window_seconds:
        raise AppAuthError("app_timestamp_expired")

    body = await request.body()
    body_hash = hashlib.sha256(body).hexdigest()
    canonical = "\n".join([
        request.method.upper(),
        request.url.path,
        _normalized_query(request),
        body_hash,
        timestamp,
        nonce,
    ])
    expected = hmac.new(
        auth_cfg["secret"].encode(),
        canonical.encode(),
        hashlib.sha256,
    ).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise AppAuthError("app_signature_invalid")

    _remember_nonce(app_key, nonce, now, window_seconds)


router = APIRouter(prefix="/app", dependencies=[Depends(verify_app_signature)])


class MemberSyncBody(BaseModel):
    uid: str
    nickname: str = ""
    mobile: str = ""
    device_model: str = ""
    device_unique_id: str = ""
    platform: int = 0


class DeviceBindBody(BaseModel):
    uid: str
    device_model: str = ""
    device_unique_id: str = ""
    platform: int = 0


class AdEventBody(BaseModel):
    uid: str
    app_id: str = ""
    app_name: str = ""
    placement: str = ""
    action: str = "show"
    revenue: float = 0
    trans_id: str = ""
    device_id: str = ""
    device_model: str = ""
    device_unique_id: str = ""
    platform: int = 0
    ip: str = ""


class RiskPrecheckBody(BaseModel):
    uid: str
    trans_id: str = ""
    device_id: str = ""
    device_model: str = ""
    device_unique_id: str = ""
    platform: int = 0
    ip: str = ""


def _clean_uid(uid: str) -> str:
    return (uid or "").strip()


def _client_ip(request: Request, fallback: str = "") -> str:
    if fallback:
        return fallback.strip()
    return request.client.host if request.client else ""


def _get_or_create_member(db: Session, uid: str) -> Member:
    member = db.query(Member).filter(Member.uid == uid).first()
    if member:
        return member
    member = Member(uid=uid, nickname=f"User {uid}")
    db.add(member)
    db.flush()
    return member


def _apply_member_fields(member: Member, nickname: str = "", mobile: str = "") -> None:
    if nickname:
        member.nickname = nickname.strip()
    if mobile:
        member.mobile = mobile.strip()
    member.last_active = datetime.utcnow()


def _member_payload(member: Member) -> dict:
    return {
        "uid": member.uid,
        "nickname": member.nickname,
        "mobile": member.mobile,
        "agent_type": member.agent_type,
        "level_id": member.level_id,
        "status": member.status,
        "is_black": member.is_black,
        "total_revenue": member.total_revenue,
        "today_revenue": member.today_revenue,
        "estimated_balance": member.estimated_balance,
        "confirmed_balance": member.confirmed_balance,
        "withdrawable_balance": member.withdrawable_balance,
        "pending_balance": member.pending_balance,
        "device_model": member.device_model or "",
        "device_unique_id": member.device_unique_id or "",
        "ad_count": member.ad_count,
        "created_at": member.created_at.isoformat(),
        "last_active": member.last_active.isoformat(),
    }


def _device_payload(device: MemberDevice | None) -> dict | None:
    if not device:
        return None
    return {
        "id": device.id,
        "uid": device.uid,
        "device_model": device.device_model,
        "device_unique_id": device.device_unique_id or "",
        "platform": device.platform,
        "source": device.source,
        "created_at": device.created_at.isoformat(),
        "updated_at": device.updated_at.isoformat(),
    }


def _transaction_payload(tx: IncentiveTransaction) -> dict:
    return {
        "trans_id": tx.trans_id,
        "uid": tx.uid,
        "app_id": tx.app_id,
        "placement_id": tx.placement_id,
        "network_code": tx.network_code,
        "network_verified": tx.network_verified,
        "taku_verified": tx.taku_verified,
        "revenue": tx.revenue,
        "user_reward": tx.user_reward,
        "status": tx.status,
        "risk_score": tx.risk_score,
        "risk_passed": tx.risk_passed,
        "remark": tx.remark,
        "created_at": tx.created_at.isoformat(),
        "confirmed_at": tx.confirmed_at.isoformat() if tx.confirmed_at else "",
    }


def _public_config(db: Session) -> dict:
    cfg = get_config_map(db)
    return {key: cfg.get(key, "") for key in PUBLIC_CONFIG_KEYS}


def _taku_app_payload(app: TakuApp) -> dict:
    return {
        "app_id": app.app_id,
        "app_name": app.app_name,
        "platform": app.platform,
        "package_name": app.package_name,
        "synced_at": app.synced_at.isoformat(),
    }


def _callback_urls() -> dict:
    return {
        "kuaishou": "/mas/callback/kuaishou/reward",
        "tencent": "/mas/callback/tencent/reward",
        "baidu": "/mas/callback/baidu/reward",
        "taku": "/mas/callback/taku/s2s",
    }


@router.get("/config")
def app_config(db: Session = Depends(get_db)):
    apps = db.query(TakuApp).order_by(TakuApp.id.desc()).all()
    return ok({
        "config": _public_config(db),
        "taku_apps": [_taku_app_payload(app) for app in apps],
        "callback_urls": _callback_urls(),
    })


@router.post("/member/sync")
def app_member_sync(body: MemberSyncBody, db: Session = Depends(get_db)):
    uid = _clean_uid(body.uid)
    if not uid:
        return fail("uid_required")

    member = _get_or_create_member(db, uid)
    _apply_member_fields(member, body.nickname, body.mobile)

    device = None
    if body.device_model or body.device_unique_id:
        device = bind_member_device(
            db,
            uid,
            body.device_model,
            body.device_unique_id,
            body.platform,
            "app",
        )

    db.commit()
    db.refresh(member)
    return ok({
        "member": _member_payload(member),
        "device": _device_payload(device),
        "config": _public_config(db),
    })


@router.post("/device/bind")
def app_device_bind(body: DeviceBindBody, db: Session = Depends(get_db)):
    uid = _clean_uid(body.uid)
    if not uid:
        return fail("uid_required")

    device = bind_member_device(
        db,
        uid,
        body.device_model,
        body.device_unique_id,
        body.platform,
        "app",
    )
    if not device:
        return fail("device_info_required")

    db.commit()
    member = db.query(Member).filter(Member.uid == uid).first()
    return ok({
        "member": _member_payload(member),
        "device": _device_payload(device),
    })


@router.get("/member/profile")
def app_member_profile(uid: str, db: Session = Depends(get_db)):
    uid = _clean_uid(uid)
    if not uid:
        return fail("uid_required")

    member = db.query(Member).filter(Member.uid == uid).first()
    if not member:
        return fail("member_not_found", 404)

    devices = (
        db.query(MemberDevice)
        .filter(MemberDevice.uid == uid)
        .order_by(MemberDevice.updated_at.desc())
        .limit(5)
        .all()
    )
    return ok({
        "member": _member_payload(member),
        "devices": [_device_payload(device) for device in devices],
    })


@router.get("/member/transactions")
def app_member_transactions(
    uid: str,
    page: int = Query(1, ge=1),
    limit: int = Query(20, ge=1, le=100),
    status: str = "",
    db: Session = Depends(get_db),
):
    uid = _clean_uid(uid)
    if not uid:
        return fail("uid_required")

    query = db.query(IncentiveTransaction).filter(IncentiveTransaction.uid == uid)
    if status:
        query = query.filter(IncentiveTransaction.status == status)

    total = query.count()
    items = (
        query.order_by(IncentiveTransaction.id.desc())
        .offset((page - 1) * limit)
        .limit(limit)
        .all()
    )
    return ok({
        "list": [_transaction_payload(tx) for tx in items],
        "total": total,
    })


@router.get("/reward/status")
def app_reward_status(
    trans_id: str,
    uid: str = "",
    db: Session = Depends(get_db),
):
    trans_id = (trans_id or "").strip()
    if not trans_id:
        return fail("trans_id_required")

    query = db.query(IncentiveTransaction).filter(IncentiveTransaction.trans_id == trans_id)
    uid = _clean_uid(uid)
    if uid:
        query = query.filter(IncentiveTransaction.uid == uid)

    tx = query.first()
    if not tx:
        return fail("transaction_not_found", 404)
    return ok(_transaction_payload(tx))


@router.post("/risk/precheck")
def app_risk_precheck(
    body: RiskPrecheckBody,
    request: Request,
    db: Session = Depends(get_db),
):
    uid = _clean_uid(body.uid)
    if not uid:
        return fail("uid_required")

    _get_or_create_member(db, uid)
    if body.device_model or body.device_unique_id:
        bind_member_device(
            db,
            uid,
            body.device_model,
            body.device_unique_id,
            body.platform,
            "app",
        )

    device_id = body.device_id or body.device_unique_id
    passed, score, hits = evaluate_risk(
        db,
        uid,
        device_id,
        _client_ip(request, body.ip),
        body.trans_id,
    )
    db.commit()
    return ok({"passed": passed, "risk_score": score, "hits": hits})


@router.post("/ad/event")
def app_ad_event(
    body: AdEventBody,
    request: Request,
    db: Session = Depends(get_db),
):
    uid = _clean_uid(body.uid)
    if not uid:
        return fail("uid_required")

    member = _get_or_create_member(db, uid)
    member.last_active = datetime.utcnow()
    device = None
    if body.device_model or body.device_unique_id:
        device = bind_member_device(
            db,
            uid,
            body.device_model,
            body.device_unique_id,
            body.platform,
            "app",
        )

    device_id = body.device_id or body.device_unique_id
    passed, score, hits = evaluate_risk(
        db,
        uid,
        device_id,
        _client_ip(request, body.ip),
        body.trans_id,
    )

    action = (body.action or "show").strip() or "show"
    if action == "show":
        member.ad_count += 1

    event = AdLog(
        uid=uid,
        app_name=body.app_name or body.app_id,
        placement=body.placement,
        revenue=body.revenue,
        action=action,
    )
    db.add(event)
    db.commit()
    db.refresh(event)
    db.refresh(member)

    return ok({
        "event": {
            "id": event.id,
            "uid": event.uid,
            "app_name": event.app_name,
            "placement": event.placement,
            "revenue": event.revenue,
            "action": event.action,
            "created_at": event.created_at.isoformat(),
        },
        "member": _member_payload(member),
        "device": _device_payload(device),
        "risk": {"passed": passed, "risk_score": score, "hits": hits},
    })
