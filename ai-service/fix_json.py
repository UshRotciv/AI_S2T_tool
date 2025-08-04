import json

with open('../app-server/scenarios.json', 'r', encoding='utf-8') as f:
    content = f.read()

# Remove the outer brackets and split by the comma that separates the objects
content = content.strip()[1:-1]
scenarios = json.loads(f'[{content}]')

with open('../app-server/scenarios.json', 'w', encoding='utf-8') as f:
    json.dump({"data": scenarios}, f, ensure_ascii=False, indent=2)
