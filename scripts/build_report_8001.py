import json, os
DIR=os.path.join(os.path.dirname(__file__),'output')
PAIRS=[('title','dbg_title.json','ask_title.json'),('questionLabel','dbg_questionLabel.json','ask_questionLabel.json'),('nlp','dbg_nlp.json','ask_nlp.json'),('ood','dbg_ood.json','ask_ood.json')]

def load(name):
  p=os.path.join(DIR,name)
  with open(p,'r',encoding='utf-8') as f:
    return json.load(f)

report={'status':load('status.json'),'tests':{}}
for key,dbg,ask in PAIRS:
  dbg_obj=load(dbg)
  ask_obj=load(ask)
  dbg_ids=[(it.get('id'),it.get('title'),it.get('distance')) for it in (dbg_obj.get('results') or [])[:5]] if isinstance(dbg_obj,dict) and 'results' in dbg_obj else dbg_obj
  if isinstance(ask_obj,dict) and 'answer' in ask_obj:
    ans=(ask_obj.get('answer') or '')
    ans=ans[:200]
    srcs=[(s.get('id'), (s.get('metadata') or {}).get('title'), s.get('distance')) for s in (ask_obj.get('sources') or [])[:5]]
    report['tests'][key]={'debug_ids':dbg_ids,'answer_head':ans,'ask_source_ids':srcs}
  else:
    report['tests'][key]={'debug_ids':dbg_ids,'ask_raw':ask_obj}

out=os.path.join(os.path.dirname(__file__),'report_8001.json')
with open(out,'w',encoding='utf-8') as f:
  json.dump(report,f,ensure_ascii=False,indent=2)
print('Wrote',out)
