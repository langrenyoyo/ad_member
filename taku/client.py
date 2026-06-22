"""
Taku (TopOn) 聚合平台 OpenAPI 客户端。

鉴权方式: X-Up-Key + X-Up-Timestamp + X-Up-Signature (MD5)
文档: https://help.takuad.com/docs/9NzgWP
"""
import hashlib
import json
import time
import urllib.parse
from typing import Any, Optional

import requests

DEFAULT_BASE_URL = "https://openapi.toponad.com"
CONTENT_TYPE = "application/json"


def _empty_body_md5() -> str:
    return hashlib.md5(b"").hexdigest().upper()


def _body_md5(body: str) -> str:
    return hashlib.md5(body.encode("utf-8")).hexdigest().upper()


def _build_signature(
    http_method: str,
    resource_path: str,
    publisher_key: str,
    timestamp_ms: int,
    body: str = "",
    content_type: str = CONTENT_TYPE,
) -> str:
    content_md5 = _body_md5(body) if body else _empty_body_md5()
    headers_str = f"X-Up-Key:{publisher_key}\nX-Up-Timestamp:{timestamp_ms}"
    sign_string = (
        f"{http_method.upper()}\n"
        f"{content_md5}\n"
        f"{content_type}\n"
        f"{headers_str}\n"
        f"{resource_path}"
    )
    return hashlib.md5(sign_string.encode("utf-8")).hexdigest().upper()


class TakuClient:
  """Taku OpenAPI 客户端，支持开发者后台管理 API 与数据报表 API。"""

  def __init__(
      self,
      publisher_key: str,
      base_url: str = DEFAULT_BASE_URL,
      timeout: int = 30,
  ):
    self.publisher_key = publisher_key
    self.base_url = base_url.rstrip("/")
    self.timeout = timeout
    self._session = requests.Session()

  def _auth_headers(self, http_method: str, resource_path: str, body: str = "") -> dict:
    timestamp_ms = int(time.time() * 1000)
    signature = _build_signature(
        http_method,
        resource_path,
        self.publisher_key,
        timestamp_ms,
        body,
    )
    return {
        "X-Up-Key": self.publisher_key,
        "X-Up-Timestamp": str(timestamp_ms),
        "X-Up-Signature": signature,
        "Content-Type": CONTENT_TYPE,
    }

  def request(
      self,
      method: str,
      path: str,
      json_body: Optional[dict] = None,
      params: Optional[dict] = None,
  ) -> Any:
    resource_path = path.split("?")[0]
    if not resource_path.startswith("/"):
      resource_path = "/" + resource_path

    body_str = ""
    if json_body is not None:
      body_str = json.dumps(json_body, ensure_ascii=False, separators=(",", ":"))

    headers = self._auth_headers(method, resource_path, body_str)
    url = f"{self.base_url}{path}"

    if method.upper() == "GET":
      response = self._session.get(
          url, headers=headers, params=params, timeout=self.timeout
      )
    elif method.upper() == "POST":
      response = self._session.post(
          url, headers=headers, data=body_str, timeout=self.timeout
      )
    else:
      raise ValueError(f"Unsupported method: {method}")

    response.raise_for_status()
    return response.json()

  # --- 应用管理 v3 ---
  def list_apps(self, app_ids: Optional[list] = None, start: int = 0, limit: int = 100) -> Any:
    body: dict = {"start": start, "limit": limit}
    if app_ids:
      body["app_ids"] = app_ids
    return self.request("POST", "/v3/apps/list", json_body=body)

  def create_apps(self, items: list) -> Any:
    return self.request("POST", "/v3/apps", json_body={"items": items})

  # --- 广告位管理 ---
  def list_placements(self, app_ids: Optional[list] = None, start: int = 0, limit: int = 100) -> Any:
    body: dict = {"start": start, "limit": limit}
    if app_ids:
      body["app_ids"] = app_ids
    return self.request("POST", "/v1/placements", json_body=body)

  # --- 广告源 v3 ---
  def list_units(
      self,
      app_ids: Optional[list] = None,
      placement_ids: Optional[list] = None,
      start: int = 0,
      limit: int = 200,
  ) -> Any:
    params: dict = {"start": start, "limit": limit}
    if app_ids:
      params["app_ids"] = ",".join(app_ids)
    if placement_ids:
      params["placement_ids"] = ",".join(placement_ids)
    query = urllib.parse.urlencode(params)
    return self.request("GET", f"/v3/units/list?{query}")

  # --- 数据报表: 综合报表 ---
  def full_report(self, body: dict) -> Any:
    return self.request("POST", "/v2/fullreport", json_body=body)
