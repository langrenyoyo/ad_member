from datetime import datetime

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth import get_admin_id, ok
from ..database import get_db
from ..models import SystemConfig, TakuApp

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
