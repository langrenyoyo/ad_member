"""
bulvchengshiios.heciguangnian.cn 后台 mas API 客户端。

前端 baseURL: /mas/ (见 dist/js/app.*.js 模块 d70b)
登录: POST /mas/login/index  { username, password }
"""
from typing import Any, Optional

import requests


class SiteAdminClient:
  """Likeshop 定制后台 mas 模块 API 客户端。"""

  def __init__(
      self,
      base_url: str = "https://bulvchengshiios.heciguangnian.cn",
      timeout: int = 30,
  ):
    self.base_url = base_url.rstrip("/")
    self.api_prefix = f"{self.base_url}/mas"
    self.timeout = timeout
    self._session = requests.Session()
    self._session.headers.update({
        "Content-Type": "application/json",
        "X-Requested-With": "XMLHttpRequest",
        "version": "3.1.0",
    })
    self.token: Optional[str] = None

  def _url(self, path: str) -> str:
    if not path.startswith("/"):
      path = "/" + path
    return f"{self.api_prefix}{path}"

  def _request(
      self,
      method: str,
      path: str,
      params: Optional[dict] = None,
      json_body: Optional[dict] = None,
  ) -> Any:
    headers = {}
    if self.token:
      headers["token"] = self.token

    response = self._session.request(
        method,
        self._url(path),
        params=params,
        json=json_body,
        headers=headers,
        timeout=self.timeout,
    )
    data = response.json()
    # 成功码为 0；部分接口直接返回数据无 code 字段
    if isinstance(data, dict) and "code" in data and data.get("code") not in (0, None):
      raise RuntimeError(f"API error code={data.get('code')} msg={data.get('msg')}")
    return data

  def login(self, username: str, password: str) -> Any:
    data = self._request("POST", "/login/index", json_body={
        "username": username,
        "password": password,
    })
    token = data.get("token") or data.get("data", {}).get("token")
    if token:
      self.token = token
    return data

  def logout(self) -> Any:
    return self._request("GET", "/login/logout")

  def get_admin_info(self) -> Any:
    return self._request("GET", "/auth.admin/getAdminInfo")

  # --- Taku 应用同步 ---
  def get_taku_apps(self) -> Any:
    """GET /core/cron/takuapps — 从 Taku 同步的应用列表。"""
    return self._request("GET", "/core/cron/takuapps")

  # --- 游戏用户管理 / 分销概览 ---
  def get_overview(self) -> Any:
    """GET /index/index — 分销数据概览（累计/今日广告收益、用户数等）。"""
    return self._request("GET", "/index/index")

  def get_active_members(self, time: str) -> Any:
    """GET /index/member — 指定日期活跃用户。"""
    return self._request("GET", "/index/member", params={"time": time})

  def list_members(self, params: Optional[dict] = None) -> Any:
    """GET /member/index — 用户列表。"""
    return self._request("GET", "/member/index", params=params or {})

  def get_member_edit(self, params: dict) -> Any:
    return self._request("GET", "/member/edit", params=params)

  def list_member_promotion(self, params: Optional[dict] = None) -> Any:
    return self._request("GET", "/member/promotion", params=params or {})

  def list_white_list(self, params: Optional[dict] = None) -> Any:
    return self._request("GET", "/member/withe_list", params=params or {})

  def get_member_more_adver_log(self, params: dict) -> Any:
    """用户广告观看明细。"""
    return self._request("GET", "/member/more_adver_log", params=params)

  def get_member_more_app(self, params: dict) -> Any:
    return self._request("GET", "/member/more_app", params=params)

  def blacklist_member(self, params: dict) -> Any:
    return self._request("GET", "/member/toblack", params=params)

  def open_member(self, body: dict) -> Any:
    return self._request("POST", "/distribution.distribution_member/open", json_body=body)

  def freeze_member(self, body: dict) -> Any:
    return self._request("POST", "/distribution.distribution_member/freeze", json_body=body)

  def list_distribution_levels(self, params: Optional[dict] = None) -> Any:
    return self._request("GET", "/distribution.distribution_level/lists", params=params or {})

  # --- 广告风控 ---
  def get_daily_report(self, params: Optional[dict] = None) -> Any:
    return self._request("GET", "/adandrisk/dailyreport", params=params or {})

  def get_adver_log(self, params: Optional[dict] = None) -> Any:
    return self._request("GET", "/adandrisk/adver_log", params=params or {})

  def get_containment_log(self, params: Optional[dict] = None) -> Any:
    return self._request("GET", "/adandrisk/containment_log", params=params or {})
