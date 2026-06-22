import re

content = open("d:/Ai/ad_member/app.js", "r", encoding="utf-8").read()

# All route-like paths
routes = set(re.findall(r"path:\s*['\"]([^'\"]+)['\"]", content))
print("=== Routes ===")
for r in sorted(routes):
    if any(k in r for k in ["game", "app", "user", "application", "taku", "ad"]):
        print(r)

# Find login API call - search for username password Promise
for m in re.finditer(r"username.*?password", content):
    ctx = content[m.start()-50:m.start()+400]
    if "Promise" in ctx or "login" in ctx.lower():
        print("\n=== Login context ===")
        print(ctx[:400])
        break

# Search API module definitions
for m in re.finditer(r"function\s+O[a-z]\(", content):
    print("API fn at", m.start())

# Find baseURL or adminapi
for pat in ["baseURL", "adminapi", "BASE_URL", "axios"]:
    idx = 0
    while True:
        idx = content.find(pat, idx)
        if idx == -1:
            break
        print(f"\n--- {pat} at {idx} ---")
        print(content[max(0,idx-80):idx+120])
        idx += len(pat)
        if idx > 200000:
            break
