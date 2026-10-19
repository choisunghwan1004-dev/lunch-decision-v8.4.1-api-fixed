import hashlib,json,re
from datetime import date
from urllib.parse import urlsplit
TYPES={'text','date','date_range','number','price','place','time'}
def validate_source(s):
 org=str(s.get('organization') or '').strip(); title=str(s.get('source_title') or '').strip(); url=str(s.get('source_url') or '').strip()
 x=urlsplit(url)
 if not org or not title or len(org)>200 or len(title)>300:raise ValueError('출처 기관명 및 제목이 필요합니다.')
 if x.scheme!='https' or not x.hostname or x.username or x.password or len(url)>1024:raise ValueError('https 출처 URL이 필요합니다.')
 return org,title,url
def validate_fact(f):
 key=str(f.get('fact_key') or '').strip();typ=str(f.get('fact_type') or '').strip();v=str(f.get('value_text') or '').strip()
 if not re.fullmatch(r'[A-Za-z0-9_-]{2,80}',key):raise ValueError('Fact Key는 영문·숫자·_·- 2~80자입니다.')
 if typ not in TYPES or not v or len(v)>4000:raise ValueError('Fact 유형이나 내용을 확인하세요.')
 if typ in ('number','price') and f.get('value_number') is None:raise ValueError('수치 Fact에 value_number가 필요합니다.')
 a,b=f.get('event_start'),f.get('event_end')
 if a and b and date.fromisoformat(str(b))<date.fromisoformat(str(a)):raise ValueError('종료일이 시작일보다 빠릅니다.')
 return key,typ,v
def can_verify(f,evidence_count,confirmed,note):
 validate_fact(f)
 if not evidence_count:raise ValueError('원자료 출처 연결이 필요합니다.')
 if not confirmed or not str(note or '').strip():raise ValueError('원문 직접 대조 체크 및 검증 의견이 필요합니다.')
 return True
def snapshot(facts):
 return [{'fact_key':x['fact_key'],'fact_type':x['fact_type'],'value_text':x['value_text'],
  'value_number':str(x['value_number']) if x.get('value_number') is not None else None,
  'unit':x.get('unit'),'event_start':str(x.get('event_start') or ''),'event_end':str(x.get('event_end') or '')}
  for x in sorted(facts,key=lambda f:f['fact_key'])]
def fingerprint(facts):
 return hashlib.sha256(json.dumps(snapshot(facts),ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def parse_draft(raw,keys):
 try:d=json.loads(raw)
 except Exception as e:raise ValueError('OpenAI가 JSON 초안을 반환하지 않았습니다.') from e
 title=str(d.get('title','')).strip();body=str(d.get('body','')).strip();claims=d.get('claims')
 if not (5<=len(title)<=200 and 40<=len(body)<=3000 and isinstance(claims,list) and 1<=len(claims)<=20):raise ValueError('기사 제목·본문·근거 문장을 확인하세요.')
 for c in claims:
  if not isinstance(c,dict) or not str(c.get('sentence','')).strip() or not isinstance(c.get('fact_keys'),list) or not c['fact_keys'] or any(k not in keys for k in c['fact_keys']):
   raise ValueError('검증되지 않은 Fact Key를 인용한 문장이 있습니다.')
 return {'title':title,'body':body,'claims':claims}
