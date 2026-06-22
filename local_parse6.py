import re

content = open("d:/Ai/ad_member/app.js", "r", encoding="utf-8").read()

# distribution routes
for m in re.finditer(r"path:"[^}]{0,300}distribution[^}]{0,300}", content):
    block = m.group()
    if "overview" in block or "distribution" in block:
        print(block[:400])
        print("---")

# Find distribution chunk references
for pat in ["distribution/overview", "distribution/"]:
    idx = 0
    while True:
        idx = content.find(pat, idx)
        if idx == -1:
            break
        print(content[max(0,idx-150):idx+250])
        print("---")
        idx += len(pat)
