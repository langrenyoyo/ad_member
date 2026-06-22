import re

content = open("d:/Ai/ad_member/app.js", "r", encoding="utf-8").read()

chinese = set(re.findall(r"[\u4e00-\u9fff]{2,30}", content))
print("=== Chinese keywords ===")
for w in sorted(chinese):
    if any(k in w for k in ["游戏", "用户", "应用", "taku", "广告", "管理", "登录"]):
        print(w)

print("\n=== Path-like strings ===")
paths = set(re.findall(r'"([a-z][a-z0-9_/]{3,60})"', content))
for p in sorted(paths):
    if "/" in p or "api" in p.lower():
        print(p)

print("\n=== account/login context ===")
idx = content.find("login")
while idx != -1:
    print(content[max(0, idx-80):idx+80])
    idx = content.find("login", idx + 1)
    if idx > 50000:
        break
