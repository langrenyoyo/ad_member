from typing import Optional

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth import get_admin_id, ok
from ..database import get_db
from ..models import DistributionLevel, Member, MemberDevice, WhiteList
from ..services.device_service import bind_member_device
from ..services.member_service import member_detail, member_stats

router = APIRouter()


def _member_item(m: Member) -> dict:
    return {
        "id": m.id,
        "uid": m.uid,
        "nickname": m.nickname,
        "mobile": m.mobile,
        "agent_type": m.agent_type,
        "level_id": m.level_id,
        "status": m.status,
        "total_revenue": m.total_revenue,
        "today_revenue": m.today_revenue,
        "estimated_balance": m.estimated_balance,
        "confirmed_balance": m.confirmed_balance,
        "withdrawable_balance": m.withdrawable_balance,
        "pending_balance": m.pending_balance,
        "device_model": m.device_model or "",
        "device_unique_id": m.device_unique_id or "",
        "ad_count": m.ad_count,
        "is_black": m.is_black,
        "created_at": m.created_at.isoformat(),
        "last_active": m.last_active.isoformat(),
    }


@router.get("/member/stats")
def member_stats_api(admin_id: int = Depends(get_admin_id), db: Session = Depends(get_db)):
    return ok(member_stats(db))


@router.get("/member/detail")
def member_detail_api(uid: str, admin_id: int = Depends(get_admin_id), db: Session = Depends(get_db)):
    m = db.query(Member).filter(Member.uid == uid).first()
    if not m:
        return {"code": 1, "msg": "用户不存在"}
    extra = member_detail(db, uid) or {}
    return ok({**_member_item(m), **extra})


@router.get("/member/index")
def member_index(
    page: int = 1,
    limit: int = 20,
    agent: Optional[str] = None,
    keyword: Optional[str] = None,
    status: Optional[int] = None,
    is_black: Optional[int] = None,
    device_unique_id: Optional[str] = None,
    abnormal: Optional[int] = None,
    sort: str = "last_active",
    admin_id: int = Depends(get_admin_id),
    db: Session = Depends(get_db),
):
    q = db.query(Member)

    if agent is not None and agent != "":
        if agent == "promoter":
            q = q.filter(Member.agent_type > 0)
        else:
            try:
                q = q.filter(Member.agent_type == int(agent))
            except ValueError:
                pass

    if keyword:
        q = q.filter(
            (Member.uid.contains(keyword))
            | (Member.nickname.contains(keyword))
            | (Member.mobile.contains(keyword))
            | (Member.device_unique_id.contains(keyword))
        )

    if device_unique_id:
        q = q.filter(Member.device_unique_id.contains(device_unique_id))

    if status is not None:
        q = q.filter(Member.status == status)

    if is_black is not None:
        q = q.filter(Member.is_black == bool(is_black))

    if abnormal:
        q = q.filter((Member.status == 0) | (Member.is_black == True))

    sort_cols = {
        "last_active": Member.last_active.desc(),
        "total_revenue": Member.total_revenue.desc(),
        "today_revenue": Member.today_revenue.desc(),
        "withdrawable_balance": Member.withdrawable_balance.desc(),
        "pending_balance": Member.pending_balance.desc(),
        "created_at": Member.created_at.desc(),
    }
    order = sort_cols.get(sort, Member.last_active.desc())

    total = q.count()
    items = q.order_by(order).offset((page - 1) * limit).limit(limit).all()
    return ok(list=[_member_item(m) for m in items], total=total)


@router.get("/member/edit")
def member_edit(uid: str, admin_id: int = Depends(get_admin_id), db: Session = Depends(get_db)):
    m = db.query(Member).filter(Member.uid == uid).first()
    if not m:
        return {"code": 1, "msg": "用户不存在"}
    return ok(_member_item(m))


@router.get("/member/promotion")
def member_promotion(
    page: int = 1,
    limit: int = 20,
    admin_id: int = Depends(get_admin_id),
    db: Session = Depends(get_db),
):
    q = db.query(Member).filter(Member.agent_type > 0)
    total = q.count()
    items = q.order_by(Member.total_revenue.desc()).offset((page - 1) * limit).limit(limit).all()
    return ok(list=[_member_item(m) for m in items], total=total)


@router.get("/member/withe_list")
def white_list(
    page: int = 1,
    limit: int = 20,
    admin_id: int = Depends(get_admin_id),
    db: Session = Depends(get_db),
):
    q = db.query(WhiteList)
    total = q.count()
    items = q.order_by(WhiteList.id.desc()).offset((page - 1) * limit).limit(limit).all()
    return ok(list=[{
        "id": w.id,
        "uid": w.uid,
        "remark": w.remark,
        "status": w.status,
        "created_at": w.created_at.isoformat(),
    } for w in items], total=total)


class WhiteBody(BaseModel):
    uid: str
    remark: str = ""


@router.get("/member/add_withe_list")
def add_white(uid: str, remark: str = "", admin_id: int = Depends(get_admin_id), db: Session = Depends(get_db)):
    db.add(WhiteList(uid=uid, remark=remark, status=1))
    db.commit()
    return ok()


@router.get("/member/delete_withe_list")
def delete_white(id: int, admin_id: int = Depends(get_admin_id), db: Session = Depends(get_db)):
    w = db.get(WhiteList, id)
    if w:
        db.delete(w)
        db.commit()
    return ok()


@router.get("/member/more_adver_log")
def more_adver_log(
    uid: str,
    page: int = 1,
    limit: int = 20,
    admin_id: int = Depends(get_admin_id),
    db: Session = Depends(get_db),
):
    from ..models import AdLog
    q = db.query(AdLog).filter(AdLog.uid == uid)
    total = q.count()
    items = q.order_by(AdLog.id.desc()).offset((page - 1) * limit).limit(limit).all()
    return ok(list=[{
        "id": a.id,
        "app_name": a.app_name,
        "placement": a.placement,
        "revenue": a.revenue,
        "action": a.action,
        "created_at": a.created_at.isoformat(),
    } for a in items], total=total)


@router.get("/member/toblack")
def toblack(uid: str, admin_id: int = Depends(get_admin_id), db: Session = Depends(get_db)):
    m = db.query(Member).filter(Member.uid == uid).first()
    if m:
        m.is_black = True
        m.status = 0
        db.commit()
    return ok()


class MemberActionBody(BaseModel):
    uid: str


@router.post("/distribution.distribution_member/open")
def member_open(body: MemberActionBody, admin_id: int = Depends(get_admin_id), db: Session = Depends(get_db)):
    m = db.query(Member).filter(Member.uid == body.uid).first()
    if m:
        m.status = 1
        m.is_black = False
        db.commit()
    return ok()


@router.post("/distribution.distribution_member/freeze")
def member_freeze(body: MemberActionBody, admin_id: int = Depends(get_admin_id), db: Session = Depends(get_db)):
    m = db.query(Member).filter(Member.uid == body.uid).first()
    if m:
        m.status = 0
        db.commit()
    return ok()


class DeviceBindBody(BaseModel):
    uid: str
    device_model: str = ""
    device_unique_id: str = ""
    platform: int = 0


@router.post("/member/device/bind")
def device_bind(body: DeviceBindBody, db: Session = Depends(get_db)):
    """客户端上报设备绑定；唯一标识获取不到时传空即可。"""
    row = bind_member_device(
        db,
        body.uid,
        body.device_model,
        body.device_unique_id,
        body.platform,
        "client",
    )
    if not row:
        return {"code": 1, "msg": "请至少提供设备型号或唯一标识"}
    db.commit()
    return ok({
        "uid": body.uid,
        "device_model": row.device_model,
        "device_unique_id": row.device_unique_id,
        "platform": row.platform,
    })


@router.get("/member/devices")
def member_devices(
    uid: str,
    admin_id: int = Depends(get_admin_id),
    db: Session = Depends(get_db),
):
    items = (
        db.query(MemberDevice)
        .filter(MemberDevice.uid == uid)
        .order_by(MemberDevice.updated_at.desc())
        .all()
    )
    return ok(list=[{
        "id": d.id,
        "uid": d.uid,
        "device_model": d.device_model,
        "device_unique_id": d.device_unique_id or "",
        "platform": d.platform,
        "source": d.source,
        "created_at": d.created_at.isoformat(),
        "updated_at": d.updated_at.isoformat(),
    } for d in items], total=len(items))


@router.get("/distribution.distribution_level/lists")
def level_lists(admin_id: int = Depends(get_admin_id), db: Session = Depends(get_db)):
    levels = db.query(DistributionLevel).all()
    return ok(list=[{"id": l.id, "name": l.name, "rate": l.rate} for l in levels])
