import re

content = open("d:/Ai/ad_member/app.js", "r", encoding="utf-8").read()

# Find application_app chunk
idx = content.find("application_app")
while idx != -1:
    print(content[max(0,idx-200):idx+300])
    print("---")
    idx = content.find("application_app", idx + 1)

# Find all chunk references near application
for m in re.finditer(r'name:"application[^"]*"[^}]{0,500}', content):
    print("\n=== application route block ===")
    print(m.group()[:500])

# Search game user in entire file  
for term in ["game_user", "gameUser", "GameUser", "游戏用户", "game_user_list"]:
    if term in content:
        print(f"Found: {term}")
