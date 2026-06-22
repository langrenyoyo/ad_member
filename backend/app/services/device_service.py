from datetime import datetime

from sqlalchemy.orm import Session

from ..models import Member, MemberDevice

_UNIQUE_KEYS = (
    "device_unique_id",
    "deviceUniqueId",
    "oaid",
    "idfa",
    "android_id",
    "androidId",
    "unique_id",
    "uniqueId",
    "imei",
)

_MODEL_KEYS = (
    "device_model",
    "deviceModel",
    "model",
    "phone_model",
    "phoneModel",
    "device_type",
    "deviceType",
)


def _pick_str(params: dict, keys: tuple[str, ...]) -> str:
    for key in keys:
        val = params.get(key)
        if val is not None and str(val).strip():
            return str(val).strip()
    return ""


def extract_device_info(params: dict) -> tuple[str, str, int]:
    """从请求参数解析设备型号与唯一标识；无唯一标识时返回空字符串。"""
    device_model = _pick_str(params, _MODEL_KEYS)
    device_unique_id = _pick_str(params, _UNIQUE_KEYS)

    platform = 0
    raw_platform = params.get("platform") or params.get("os") or params.get("device_os")
    if raw_platform is not None:
        p = str(raw_platform).lower()
        if p in ("1", "android", "andr"):
            platform = 1
        elif p in ("2", "ios", "iphone"):
            platform = 2
        elif str(raw_platform) == "1":
            platform = 1
        elif str(raw_platform) == "2":
            platform = 2

    return device_model, device_unique_id, platform


def bind_member_device(
    db: Session,
    uid: str,
    device_model: str = "",
    device_unique_id: str = "",
    platform: int = 0,
    source: str = "client",
) -> MemberDevice | None:
    """绑定用户与设备；唯一标识获取不到时留空，仅记录型号。"""
    if not uid:
        return None

    device_model = (device_model or "").strip()
    device_unique_id = (device_unique_id or "").strip()

    if not device_model and not device_unique_id:
        return None

    member = db.query(Member).filter(Member.uid == uid).first()
    if not member:
        member = Member(uid=uid, nickname=f"用户{uid}")
        db.add(member)
        db.flush()

    member.device_model = device_model
    member.device_unique_id = device_unique_id
    member.last_active = datetime.utcnow()

    now = datetime.utcnow()
    if device_unique_id:
        row = db.query(MemberDevice).filter(
            MemberDevice.uid == uid,
            MemberDevice.device_unique_id == device_unique_id,
        ).first()
    else:
        row = db.query(MemberDevice).filter(
            MemberDevice.uid == uid,
            MemberDevice.device_unique_id == "",
            MemberDevice.device_model == device_model,
        ).first()

    if row:
        row.device_model = device_model
        row.platform = platform
        row.source = source
        row.updated_at = now
    else:
        row = MemberDevice(
            uid=uid,
            device_model=device_model,
            device_unique_id=device_unique_id,
            platform=platform,
            source=source,
            created_at=now,
            updated_at=now,
        )
        db.add(row)

    return row


def bind_member_device_from_params(
    db: Session,
    uid: str,
    params: dict,
    source: str = "callback",
) -> MemberDevice | None:
    model, unique_id, platform = extract_device_info(params)
    return bind_member_device(db, uid, model, unique_id, platform, source)
