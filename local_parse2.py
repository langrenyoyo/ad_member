import re

content = open("d:/Ai/ad_member/app.js", "r", encoding="utf-8").read()

# Find unicode escaped chinese
escaped = set(re.findall(r"\\u[0-9a-fA-F]{4}", content))
# decode unicode escapes in chunks
parts = re.findall(r'(?:\\u[0-9a-fA-F]{4})+', content)
decoded_words = set()
for p in parts:
    try:
        s = p.encode().decode('unicode_escape')
        if any('\u4e00' <= c <= '\u9fff' for c in s):
            decoded_words.add(s)
    except Exception:
        pass

print("=== Decoded unicode strings (game/app related) ===")
for w in sorted(decoded_words):
    if any(k in w for k in ["游戏", "用户", "应用", "taku", "广告", "管理"]):
        print(w)

# Find API function patterns Ob, etc
for pat in ["Ob(", "account/", "game", "taku", "Taku", "application"]:
    indices = [m.start() for m in re.finditer(pat, content, re.I)]
    print(f"\n=== '{pat}' count: {len(indices)} ===")
    for idx in indices[:5]:
        print(content[max(0,idx-100):idx+150])

# Find login API
m = re.search(r'login\(\{commit.*?\}\)', content)
if m:
    start = m.start()
    print("\n=== Login action ===")
    print(content[start:start+500])
