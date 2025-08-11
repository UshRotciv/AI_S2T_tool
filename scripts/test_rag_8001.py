import json
import sys
import urllib.parse
import urllib.request

BASE = 'http://localhost:8001'

def http_get(url):
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            data = r.read().decode('utf-8', errors='replace')
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return {"raw": data}
    except Exception as e:
        return {"error": str(e), "url": url}


def http_post_json(url, payload):
    try:
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=120) as r:
            body = r.read().decode('utf-8', errors='replace')
            try:
                return json.loads(body)
            except json.JSONDecodeError:
                return {"raw": body}
    except Exception as e:
        return {"error": str(e), "url": url, "payload": payload}


def main():
    tests = [
        {"name": "標題測試", "q": "印表機發現無人拿走的機密文件"},
        {"name": "questionLabel測試", "q": "你在印表機旁發現一份標示著「ASUS Confidential」的設計圖，但附近沒有人。這時你該怎麼做？"},
        {"name": "資安範疇自然語言", "q": "在辦公室如果看到別人的機密文件遺留在印表機該怎麼處理才最合規？"},
        {"name": "範疇外問題", "q": "明天台積電股票會漲嗎？"},
    ]

    print('--- 健康檢查 ---')
    print(json.dumps(http_get(f"{BASE}/api/status"), ensure_ascii=False, indent=2))
    print()

    for t in tests:
        print(f"=== {t['name']} ===")
        enc_q = urllib.parse.quote(t['q'])
        dbg = http_get(f"{BASE}/api/debug/sample?q={enc_q}&k=5")
        print('[Debug] 檢索摘要:')
        print(json.dumps(dbg, ensure_ascii=False, indent=2))
        print()
        resp = http_post_json(f"{BASE}/api/ask", {"question": t['q']})
        print('[Ask] 回答:')
        # 只輸出關鍵欄位，避免太長
        if isinstance(resp, dict) and 'answer' in resp:
            out = {
                'answer': resp.get('answer'),
                'session_id': resp.get('session_id'),
                'sources_sample': [
                    {
                        'id': s.get('id'),
                        'title': (s.get('metadata') or {}).get('title'),
                        'category': (s.get('metadata') or {}).get('category'),
                        'distance': s.get('distance'),
                    }
                    for s in (resp.get('sources') or [])[:5]
                ]
            }
            print(json.dumps(out, ensure_ascii=False, indent=2))
        else:
            print(json.dumps(resp, ensure_ascii=False, indent=2))
        print()

if __name__ == '__main__':
    sys.exit(main())
