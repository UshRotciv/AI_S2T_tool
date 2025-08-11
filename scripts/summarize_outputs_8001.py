import json
import os

dir_path = os.path.join(os.path.dirname(__file__), 'output')

def load(name):
    p = os.path.join(dir_path, name)
    try:
        with open(p, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        return {"error": str(e), "file": p}

def to_ascii(obj):
    return json.dumps(obj, ensure_ascii=True, indent=2)

pairs = [
    ("title", "dbg_title.json", "ask_title.json"),
    ("questionLabel", "dbg_questionLabel.json", "ask_questionLabel.json"),
    ("nlp", "dbg_nlp.json", "ask_nlp.json"),
    ("ood", "dbg_ood.json", "ask_ood.json"),
]

status = load('status.json')
print('--- STATUS ---')
print(to_ascii(status))
print()

for key, dbg_name, ask_name in pairs:
    print(f'=== {key} ===')
    dbg = load(dbg_name)
    ask = load(ask_name)

    # Debug 檢索摘要 Top-3
    print('[Debug Top-3]')
    if isinstance(dbg, dict) and 'results' in dbg:
        items = dbg.get('results') or []
        top_dbg = []
        for it in items[:3]:
            title = (it.get('title') or '')
            if isinstance(title, str) and len(title) > 80:
                title = title[:77] + '...'
            top_dbg.append({
               'id': it.get('id'),
               'title': title,
               'category': it.get('category'),
               'distance': it.get('distance'),
            })
        print(to_ascii(top_dbg))
    else:
        print(to_ascii(dbg if isinstance(dbg, dict) else {'raw': str(dbg)[:200]}))

    # Ask 回答與來源 Top-3
    print('[Ask Summary]')
    if isinstance(ask, dict) and 'answer' in ask:
        ans = (ask.get('answer') or '')
        if len(ans) > 120:
            ans = ans[:117] + '...'
        sources = []
        for s in (ask.get('sources') or [])[:3]:
            title = ((s.get('metadata') or {}).get('title') or '')
            if isinstance(title, str) and len(title) > 80:
                title = title[:77] + '...'
            sources.append({
                'id': s.get('id'),
                'title': title,
                'category': (s.get('metadata') or {}).get('category'),
                'distance': s.get('distance'),
            })
        out = {'answer_head': ans, 'sources_top3': sources}
    else:
        out = ask if isinstance(ask, dict) else {'raw': str(ask)[:200]}
    print(to_ascii(out))
    print()
