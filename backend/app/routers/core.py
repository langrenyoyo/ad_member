from datetime import datetime
import json

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth import fail, get_admin_id, ok
from ..database import get_db
from ..models import SystemConfig, TakuApp, TakuPlacement
from ..services.config_service import get_config_map
from ..services.taku_client import TakuClient
import requests

router = APIRouter()


@router.get("/core/cron/takuapps")
def taku_apps(admin_id: int = Depends(get_admin_id), db: Session = Depends(get_db)):
    apps = db.query(TakuApp).all()
    return ok(list=[{
        "app_id": a.app_id,
        "app_name": a.app_name,
        "platform": a.platform,
        "package_name": a.package_name,
        "kuaishou_security_key": a.kuaishou_security_key,
        "tencent_security_key": a.tencent_security_key,
        "tencent_sign_method": a.tencent_sign_method,
        "baidu_security_key": a.baidu_security_key,
        "baidu_sign_method": a.baidu_sign_method,
        "synced_at": a.synced_at.isoformat(),
    } for a in apps])


class SyncAppBody(BaseModel):
    app_id: str
    app_name: str
    platform: int = 2
    package_name: str = ""
    kuaishou_security_key: str = ""
    tencent_security_key: str = ""
    tencent_sign_method: str = "hmac_sha256"
    baidu_security_key: str = ""
    baidu_sign_method: str = "md5_secret_colon_transid"


@router.post("/core/cron/takuapps/sync")
def sync_taku_app(body: SyncAppBody, admin_id: int = Depends(get_admin_id), db: Session = Depends(get_db)):
    existing = db.query(TakuApp).filter(TakuApp.app_id == body.app_id).first()
    if existing:
        existing.app_name = body.app_name
        existing.platform = body.platform
        existing.package_name = body.package_name
        existing.kuaishou_security_key = body.kuaishou_security_key
        existing.tencent_security_key = body.tencent_security_key
        existing.tencent_sign_method = body.tencent_sign_method
        existing.baidu_security_key = body.baidu_security_key
        existing.baidu_sign_method = body.baidu_sign_method
        existing.synced_at = datetime.utcnow()
    else:
        db.add(TakuApp(
            app_id=body.app_id,
            app_name=body.app_name,
            platform=body.platform,
            package_name=body.package_name,
            kuaishou_security_key=body.kuaishou_security_key,
            tencent_security_key=body.tencent_security_key,
            tencent_sign_method=body.tencent_sign_method,
            baidu_security_key=body.baidu_security_key,
            baidu_sign_method=body.baidu_sign_method,
        ))
    db.commit()
    return ok()


def _placement_rows(payload):
    if isinstance(payload, list):
        return payload
    if isinstance(payload, dict):
        for key in ("list", "items", "placements", "data"):
            value = payload.get(key)
            rows = _placement_rows(value)
            if rows:
                return rows
    return []


def _placement_value(row, *keys, default=""):
    for key in keys:
        value = row.get(key) if isinstance(row, dict) else None
        if value not in (None, ""):
            return str(value)
    return default


def _placement_enabled(row) -> bool:
    status = row.get("status_v2", row.get("status")) if isinstance(row, dict) else None
    return status is None or str(status) == "3"


@router.get("/core/cron/takuplacements")
def taku_placements(app_id: str = "", admin_id: int = Depends(get_admin_id), db: Session = Depends(get_db)):
    app_id = app_id or get_config_map(db).get("taku_media_app_id", "")
    if not app_id:
        return fail("请先配置 TAKU 媒体 App ID")
    query = db.query(TakuPlacement)
    if app_id:
        query = query.filter(TakuPlacement.app_id == app_id)
    rows = query.order_by(TakuPlacement.synced_at.desc(), TakuPlacement.id.desc()).all()
    return ok(list=[{
        "placement_id": p.placement_id, "app_id": p.app_id,
        "placement_name": p.placement_name, "ad_format": p.ad_format,
        "platform": p.platform, "status": p.status, "synced_at": p.synced_at.isoformat(),
    } for p in rows])


class SyncPlacementBody(BaseModel):
    app_id: str = ""


@router.post("/core/cron/takuplacements/sync")
def sync_taku_placements(body: SyncPlacementBody, admin_id: int = Depends(get_admin_id), db: Session = Depends(get_db)):
    cfg = get_config_map(db)
    publisher_key = cfg.get("taku_publisher_key", "")
    if not publisher_key:
        return fail("请先配置 TAKU Publisher Key")
    media_app_id = cfg.get("taku_media_app_id", "")
    if not media_app_id:
        return fail("请先配置 TAKU 媒体 App ID")
    client = TakuClient(publisher_key, cfg.get("taku_api_base", "https://openapi.toponad.com"))
    try:
        payload = client.list_placements(app_ids=[media_app_id])
    except requests.RequestException as exc:
        return fail(f"TAKU 广告位同步失败: {exc}")
    count = 0
    active_ids = set()
    for row in _placement_rows(payload):
        if not _placement_enabled(row):
            continue
        placement_id = _placement_value(row, "placement_id", "placementId", "id")
        if not placement_id:
            continue
        active_ids.add(placement_id)
        item = db.query(TakuPlacement).filter(TakuPlacement.placement_id == placement_id).first()
        if not item:
            item = TakuPlacement(placement_id=placement_id)
            db.add(item)
        item.app_id = _placement_value(row, "app_id", "appId", "application_id", default=media_app_id)
        item.placement_name = _placement_value(row, "placement_name", "placementName", "name")
        item.ad_format = _placement_value(row, "adformat", "ad_format", "adFormat", "format", "type")
        item.platform = _placement_value(row, "platform", "os")
        item.status = "active"
        item.raw_data = json.dumps(row, ensure_ascii=False)
        item.synced_at = datetime.utcnow()
        count += 1
    stale = db.query(TakuPlacement).filter(TakuPlacement.app_id == media_app_id)
    if active_ids:
        stale = stale.filter(TakuPlacement.placement_id.notin_(active_ids))
    stale.delete(synchronize_session=False)
    db.commit()
    return ok(count=count)


@router.get("/config/index")
def config_index(admin_id: int = Depends(get_admin_id), db: Session = Depends(get_db)):
    configs = db.query(SystemConfig).all()
    return ok({c.key: c.value for c in configs})


class ConfigSaveBody(BaseModel):
    configs: dict


@router.post("/config/ConfigSaveAll")
def config_save(body: ConfigSaveBody, admin_id: int = Depends(get_admin_id), db: Session = Depends(get_db)):
    for key, value in body.configs.items():
        cfg = db.query(SystemConfig).filter(SystemConfig.key == key).first()
        if cfg:
            cfg.value = str(value)
        else:
            db.add(SystemConfig(key=key, value=str(value)))
    db.commit()
    return ok()
