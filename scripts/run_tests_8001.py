import json
import os
import urllib.parse
import urllib.request

BASE = 'http://localhost:8001'
OUTDIR = os.path.join(os.path.dirname(__file__), 'output')
os.makedirs(OUTDIR, exist_ok=True)

def http_get(url, timeout=60):
    try:
        with urllib.request.urlopen(url, timeout=timeout) as r:
            data = r.read().decode('utf-8', errors='replace')
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return {"raw": data}
    except Exception as e:
        return {"error": str(e), "url": url}


def http_post_json(url, payload, timeout=120):
    try:
        data = json.dumps(payload, ensure_ascii=False).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=timeout) as r:
            body = r.read().decode('utf-8', errors='replace')
            try:
                return json.loads(body)
            except json.JSONDecodeError:
                return {"raw": body}
    except Exception as e:
        return {"error": str(e), "url": url, "payload": payload}


def save(path, obj):
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(obj, f, ensure_ascii=False, indent=2)


def main():
    tests = [
        ("title", "印表機發現無人拿走的機密文件"),
        ("questionLabel", "你在印表機旁發現一份標示著「ASUS Confidential」的設計圖，但附近沒有人。這時你該怎麼做？"),
        ("nlp", "在辦公室如果看到別人的機密文件遺留在印表機該怎麼處理才最合規？"),
        ("ood", "明天台積電股票會漲嗎？"),
    ]

    status = http_get(f"{BASE}/api/status")
    save(os.path.join(OUTDIR, 'status.json'), status)

    for key, q in tests:
        enc = urllib.parse.quote(q)
        dbg = http_get(f"{BASE}/api/debug/sample?q={enc}&k=5")
        save(os.path.join(OUTDIR, f"dbg_{key}.json"), dbg)
        ask = http_post_json(f"{BASE}/api/ask", {"question": q})
        # 縮小 ask 結果
        if isinstance(ask, dict) and 'answer' in ask:
            slim = {
                'answer': ask.get('answer'),
                'session_id': ask.get('session_id'),
                'sources_sample': [
                    {
                        'id': s.get('id'),
                        'title': (s.get('metadata') or {}).get('title'),
                        'category': (s.get('metadata') or {}).get('category'),
                        'distance': s.get('distance'),
                    }
                    for s in (ask.get('sources') or [])[:5]
                ]
            }
            save(os.path.join(OUTDIR, f"ask_{key}.json"), slim)
        else:
            save(os.path.join(OUTDIR, f"ask_{key}.json"), ask)

    print("Wrote outputs to:", OUTDIR)

if __name__ == '__main__':
    main()
