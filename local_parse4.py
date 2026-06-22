import re

content = open("d:/Ai/ad_member/app.js", "r", encoding="utf-8").read()

# Find all /mas/ or mas/ API paths
apis = set(re.findall(r'["\']([a-zA-Z0-9_/]+)["\']', content))
mas_apis = [a for a in apis if "mas" in a.lower() or a.startswith("account") or "application" in a or "game" in a.lower()]
print("=== mas/application/game APIs ===")
for a in sorted(set(mas_apis)):
    print(a)

# Find module c for login - search account/login path
for pat in ["account/login", "account/logout", "application/", "game_user", "gameUser", "GameUser"]:
    for m in re.finditer(pat, content, re.I):
        print(f"\n--- {pat} ---")
        print(content[max(0,m.start()-60):m.start()+120])

# Find chunk mapping for application
for m in re.finditer(r"application[^\"']{0,200}", content):
    s = m.group()
    if "chunk" in s or "path" in s or "component" in s:
        print("\n", s[:200])
