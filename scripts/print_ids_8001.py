import json, os
p=os.path.join(os.path.dirname(__file__),'report_8001.json')
with open(p,'r',encoding='utf-8') as f:
  r=json.load(f)
print('STATUS:', r.get('status',{}).get('status'))
for key, sec in (r.get('tests') or {}).items():
  print('===', key, '===')
  dbg=sec.get('debug_ids')
  if isinstance(dbg,list):
    print('Debug IDs:')
    for t in dbg:
      if isinstance(t, (list, tuple)):
        id_, title, dist = (t+[None,None,None])[:3]
        print('-', id_, dist)
      else:
        print('-', str(t)[:80])
  else:
    print('Debug IDs RAW:', str(dbg)[:120])
  src=sec.get('ask_source_ids')
  if isinstance(src,list):
    print('Ask Sources:')
    for t in src:
      if isinstance(t, (list, tuple)):
        id_, title, dist = (t+[None,None,None])[:3]
        print('-', id_, dist)
      else:
        print('-', str(t)[:80])
  else:
    print('Ask RAW:', str(src)[:120])
  print()
