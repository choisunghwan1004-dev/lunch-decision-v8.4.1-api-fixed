"""Explicit live MySQL check, optional one billable OpenAI request."""
import json,os,sys,datetime
from pathlib import Path
from dotenv import load_dotenv
load_dotenv()
r={'time':datetime.datetime.now(datetime.timezone.utc).isoformat(),'mysql':{'ok':False},'openai':{'attempted':False,'ok':False}}
try:
 from db import db
 with db() as c:
  c.execute("SHOW TABLES LIKE 'news_%'")
  names=[next(iter(x.values())) for x in c.fetchall()]
  c.execute('SELECT COUNT(*) AS n FROM districts')
  r['mysql']={'ok':len(names)==10,'tables':sorted(names),'districts':c.fetchone()['n']}
except Exception as e:r['mysql']['error']=type(e).__name__+': '+str(e)[:140]
if '--openai' in sys.argv:
 r['openai']['attempted']=True
 if not os.getenv('OPENAI_API_KEY'):r['openai']['error']='OPENAI_API_KEY missing'
 else:
  try:
   from openai import OpenAI
   t=OpenAI(api_key=os.environ['OPENAI_API_KEY'],timeout=30).responses.create(model=os.getenv('OPENAI_MODEL','gpt-4.1-mini'),input='Reply exactly: TEST OK',max_output_tokens=20)
   r['openai']={'attempted':True,'ok':bool(t.output_text.strip()),'request_id':t.id,'input_tokens':t.usage.input_tokens,'output_tokens':t.usage.output_tokens}
  except Exception as e:r['openai']['error']=type(e).__name__+': '+str(e)[:140]
path=Path(__file__).parent/'diagnostics/news-live-check.json';path.parent.mkdir(exist_ok=True)
path.write_text(json.dumps(r,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
print(json.dumps(r,ensure_ascii=False,indent=2,default=str))
sys.exit(0 if r['mysql']['ok'] and (not r['openai']['attempted'] or r['openai']['ok']) else 1)
