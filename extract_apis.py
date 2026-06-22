import re
import os

# Login API in app.js
app = open("d:/Ai/ad_member/app.js", encoding="utf-8").read()
for pat in ["account/login", "account/logout", "f175"]:
    idx = app.find(pat)
    if idx >= 0:
        print(f"=== app.js {pat} ===")
        print(app[max(0, idx - 100):idx + 300])

for fn in ["chunk-overview.js", "chunk-3066802e.js", "chunk-554134ce.js"]:
    path = f"d:/Ai/ad_member/{fn}"
    if not os.path.exists(path):
        continue
    content = open(path, encoding="utf-8").read()
    print(f"=== {fn} ({len(content)} bytes) ===")
    for m in re.finditer(r"url:\s*['\"]([^'\"]+)['\"]", content):
        print("url:", m.group(1))
    for m in re.finditer(r"['\"](distribution/[a-zA-Z0-9_/]+)['\"]", content):
        print("path:", m.group(1))
    for m in re.finditer(r"['\"]([a-z]+/[a-z]+/[a-zA-Z0-9_/]+)['\"]", content):
        p = m.group(1)
        if any(k in p for k in ["distribution", "advertisement", "taku", "account", "user"]):
            print("api:", p)
