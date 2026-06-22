import hashlib
import secrets
from typing import Any, Optional

from fastapi import Header, HTTPException

_tokens: dict[str, int] = {}


def hash_password(password: str) -> str:
    return hashlib.sha256(password.encode()).hexdigest()


def create_token(admin_id: int) -> str:
    token = secrets.token_hex(32)
    _tokens[token] = admin_id
    return token


def revoke_token(token: str) -> None:
    _tokens.pop(token, None)


def get_admin_id(token: Optional[str] = Header(None, alias="token")) -> int:
    if not token or token not in _tokens:
        raise HTTPException(status_code=401, detail="未登录或 token 无效")
    return _tokens[token]


def ok(data: Any = None, **kwargs) -> dict:
    result = {"code": 0, "msg": "success"}
    if data is not None:
        result["data"] = data
    result.update(kwargs)
    return result


def fail(msg: str, code: int = 1) -> dict:
    return {"code": code, "msg": msg}
