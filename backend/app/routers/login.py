from typing import Optional

from fastapi import APIRouter, Depends, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session

from ..auth import create_token, get_admin_id, hash_password, ok, revoke_token
from ..database import get_db
from ..models import Admin

router = APIRouter()


class LoginBody(BaseModel):
    username: str
    password: str


@router.post("/login/index")
def login_index(body: LoginBody, db: Session = Depends(get_db)):
    admin = db.query(Admin).filter(Admin.username == body.username).first()
    if not admin or admin.password != hash_password(body.password):
        return {"code": 1, "msg": "账号或密码错误"}
    token = create_token(admin.id)
    return ok({
        "token": token,
        "username": admin.username,
        "name": admin.name,
        "open_shop": 1,
        "logo": "",
    }, token=token)


@router.get("/login/logout")
def login_logout(token: Optional[str] = Header(None)):
    if token:
        revoke_token(token)
    return ok()


@router.get("/auth.admin/getAdminInfo")
def get_admin_info(admin_id: int = Depends(get_admin_id), db: Session = Depends(get_db)):
    admin = db.get(Admin, admin_id)
    return ok({"username": admin.username, "name": admin.name})
