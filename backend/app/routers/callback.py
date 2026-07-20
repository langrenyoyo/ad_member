import json

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from ..database import get_db
from ..models import TakuApp
from ..services.incentive_service import (
    process_ad_network_callback,
    process_kuaishou_callback,
    process_taku_callback,
)

router = APIRouter()


async def _request_params(request: Request) -> tuple[dict, str]:
    params = dict(request.query_params)
    if request.method == "POST":
        try:
            body = await request.json()
            if isinstance(body, dict):
                params.update(body)
        except Exception:
            pass
    return params, json.dumps(params, ensure_ascii=False)


@router.get("/callback/kuaishou/reward")
@router.post("/callback/kuaishou/reward")
async def kuaishou_reward(request: Request, db: Session = Depends(get_db)):
    """快手联盟激励回调：sign = md5(appSecurityKey:transId)"""
    params = dict(request.query_params)
    if request.method == "POST":
        try:
            body = await request.json()
            if isinstance(body, dict):
                params.update(body)
        except Exception:
            pass
    raw = json.dumps(params, ensure_ascii=False)

    app_id = str(params.get("appId") or params.get("app_id") or "")
    security_key = ""
    if app_id:
        app = db.query(TakuApp).filter(TakuApp.app_id == app_id).first()
        if app:
            security_key = app.kuaishou_security_key or ""

    result = process_kuaishou_callback(db, params, security_key, raw)
    if not result.get("ok"):
        return {"isValid": False, "reason": result.get("reason")}
    return {"isValid": True, "transId": result.get("trans_id")}


async def _network_reward(request: Request, db: Session, network_code: str) -> dict:
    params, raw = await _request_params(request)
    app_id = str(params.get("appId") or params.get("app_id") or "")
    app = db.query(TakuApp).filter(TakuApp.app_id == app_id).first() if app_id else None
    if network_code == "tencent":
        secret = app.tencent_security_key if app else ""
        method = app.tencent_sign_method if app else "hmac_sha256"
    else:
        secret = app.baidu_security_key if app else ""
        method = app.baidu_sign_method if app else "md5_secret_colon_transid"
    result = process_ad_network_callback(
        db, params, network_code, secret or "", method or "", raw
    )
    if not result.get("ok"):
        return {"code": 1, "msg": result.get("reason", "callback_invalid")}
    return {"code": 0, "data": result}


@router.get("/callback/tencent/reward")
@router.post("/callback/tencent/reward")
async def tencent_reward(request: Request, db: Session = Depends(get_db)):
    return await _network_reward(request, db, "tencent")


@router.get("/callback/baidu/reward")
@router.post("/callback/baidu/reward")
async def baidu_reward(request: Request, db: Session = Depends(get_db)):
    return await _network_reward(request, db, "baidu")


@router.get("/callback/taku/s2s")
@router.post("/callback/taku/s2s")
async def taku_s2s(request: Request, db: Session = Depends(get_db)):
    """Taku S2S 回调（快手 network_firm_id=28 为辅验）。"""
    params = dict(request.query_params)
    if request.method == "POST":
        try:
            body = await request.json()
            if isinstance(body, dict):
                params.update(body)
        except Exception:
            pass
    raw = json.dumps(params, ensure_ascii=False)
    result = process_taku_callback(db, params, raw)
    return {"code": 0 if result.get("ok") else 1, "data": result}
