"""
Taku 聚合平台 + 游戏用户管理后台对接示例。

用法:
  1. 复制 config.example.env 为 .env 并填写 TAKU_PUBLISHER_KEY
  2. python main.py
"""
import os
import sys

from taku.client import TakuClient
from site.client import SiteAdminClient


def load_env_file(path: str) -> None:
  if not os.path.exists(path):
    return
  with open(path, encoding="utf-8") as f:
    for line in f:
      line = line.strip()
      if not line or line.startswith("#") or "=" not in line:
        continue
      key, _, value = line.partition("=")
      os.environ.setdefault(key.strip(), value.strip())


def main() -> None:
  load_env_file(os.path.join(os.path.dirname(__file__), ".env"))
  load_env_file(os.path.join(os.path.dirname(__file__), "config.example.env"))

  publisher_key = os.environ.get("TAKU_PUBLISHER_KEY", "")
  site_base = os.environ.get("SITE_BASE_URL", "https://bulvchengshiios.heciguangnian.cn")
  site_user = os.environ.get("SITE_USERNAME", "qdmin")
  site_pass = os.environ.get("SITE_PASSWORD", "")

  print("=== Taku OpenAPI ===")
  if not publisher_key or publisher_key == "your_publisher_key_here":
    print("请设置 TAKU_PUBLISHER_KEY（Taku 后台 -> 账号管理 -> Publisher Key）")
  else:
    taku = TakuClient(publisher_key=publisher_key)
    try:
      apps = taku.list_apps(limit=10)
      print("Taku 应用列表:", apps)
    except Exception as exc:
      print("Taku API 调用失败:", exc)

  print("\n=== 站点后台 mas API ===")
  if not site_pass:
    print("请设置 SITE_PASSWORD")
    return

  site = SiteAdminClient(base_url=site_base)
  try:
    login_result = site.login(site_user, site_pass)
    print("登录成功, token:", site.token or login_result)

    overview = site.get_overview()
    print("分销概览:", overview)

    taku_apps = site.get_taku_apps()
    print("站点已同步 Taku 应用:", taku_apps)

    members = site.list_members({"page": 1, "limit": 5})
    print("用户列表(前5):", members)
  except Exception as exc:
    print("站点 API 调用失败:", exc)
    sys.exit(1)


if __name__ == "__main__":
  main()
