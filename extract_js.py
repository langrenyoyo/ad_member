"""Extract API paths and Chinese labels from minified JS bundles."""
import re
import requests

BASE = "https://bulvchengshiios.heciguangnian.cn/dist/js/"

def extract_strings(content):
    # Chinese text
    chinese = set(re.findall(r'[\u4e00-\u9fff]{2,30}', content))
    # API-like paths
    apis = set(re.findall(r'["\'](/[a-zA-Z0-9_/.-]+(?:api|admin)[a-zA-Z0-9_/.-]*)["\']', content, re.I))
    apis |= set(re.findall(r'["\']([a-zA-Z]+/[a-zA-Z]+/[a-zA-Z0-9_]+)["\']', content))
    return chinese, apis

# Download app.js
r = requests.get(BASE + "app.1c789f4e.js", timeout=60)
content = r.text
chinese, apis = extract_strings(content)

keywords = [w for w in chinese if any(k in w for k in ['游戏', '用户', '应用', 'taku', 'Taku', '广告'])]
print("=== Keywords in app.js ===")
for w in sorted(keywords):
    print(w)

print("\n=== API paths in app.js ===")
for a in sorted(apis):
  if 'api' in a.lower() or '/' in a:
    print(a)

# Search chunk files for game user
index_html = requests.get("https://bulvchengshiios.heciguangnian.cn/dist/", timeout=30).text
chunks = re.findall(r'/dist/js/(chunk-[a-f0-9]+\.[a-f0-9]+\.js)', index_html)
print(f"\nFound {len(chunks)} chunks")

game_chunks = []
for chunk in chunks:
    try:
        c = requests.get(BASE + chunk.split('/')[-1], timeout=30).text
        if '游戏用户' in c or 'game_user' in c or 'gameUser' in c:
            game_chunks.append(chunk)
            ch, ap = extract_strings(c)
            print(f"\n=== MATCH: {chunk} ===")
            for w in sorted(ch):
                if any(k in w for k in ['游戏', '用户', '应用', 'taku', '广告', '管理']):
                    print(f"  {w}")
            for a in sorted(ap):
                if 'api' in a.lower():
                    print(f"  API: {a}")
    except Exception as e:
        pass

print(f"\nGame-related chunks: {game_chunks}")
