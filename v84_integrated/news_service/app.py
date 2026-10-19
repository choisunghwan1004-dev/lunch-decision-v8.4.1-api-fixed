"""V8.5.1 internal FastAPI, accessed only via Node administrator proxy."""
from __future__ import annotations
import os,re,hmac,hashlib
from pathlib import Path
from contextlib import contextmanager
from fastapi import FastAPI,Request,HTTPException,Header,Depends
from fastapi.responses import JSONResponse
from dotenv import load_dotenv
from .validation import validate_source,validate_fact,can_verify,fingerprint
from .article_ai import generate_article
load_dotenv(Path(__file__).resolve().parents[1]/'.env')
app=FastAPI(title='AI 지역 뉴스 V8.5.1',docs_url=None,redoc_url=None)
def auth(x_news_internal_token:str|None=Header(None)):
 key=os.getenv('NEWS_INTERNAL_TOKEN','')
 if not re.fullmatch('[0-9a-fA-F]{64}',key) or not x_news_internal_token or not hmac.compare_digest(key,x_news_internal_token):
  raise HTTPException(403,detail='뉴스 내부 인증 실패')
def bad(message,status=400):raise HTTPException(status,detail=message)
@contextmanager
def db():
 import mysql.connector
 name=os.getenv('V83_DB_NAME','lunch_decision_v83')
 if not re.fullmatch('[A-Za-z0-9_]+',name) or name==os.getenv('OLD_DB_NAME','lunch_decision'):raise RuntimeError('DB 안전 설정 오류')
 conn=mysql.connector.connect(host=os.getenv('DB_HOST','127.0.0.1'),port=int(os.getenv('DB_PORT','3306')),user=os.getenv('DB_USER','root'),password=os.getenv('DB_PASSWORD',''),database=name,charset='utf8mb4',connection_timeout=8)
 cur=conn.cursor(dictionary=True)
 try:
  yield conn,cur
  conn.commit()
 except Exception:
  conn.rollback();raise
 finally:
  cur.close();conn.close()
def one(c,q,a=()):c.execute(q,a);return c.fetchone()
def many(c,q,a=()):c.execute(q,a);return c.fetchall()
def topic(c,id):
 row=one(c,"SELECT t.*,CONCAT(p.name,' ',d.name) region_name FROM news_topics t JOIN districts d ON d.id=t.district_id JOIN provinces p ON p.id=d.province_id WHERE t.id=%s",(id,))
 if not row:bad('뉴스 주제를 찾지 못했습니다.',404)
 return row
@app.exception_handler(ValueError)
async def value_error(_,e):return JSONResponse(status_code=422,content={'detail':str(e)})
@app.get('/health',dependencies=[Depends(auth)])
def health():
 try:
  with db() as (_,c):row=one(c,'SELECT COUNT(*) n FROM news_topics')
  return {'ok':True,'schema':True,'topics':row['n'],'model':os.getenv('OPENAI_NEWS_MODEL','gpt-4.1-mini'),'openaiConfigured':bool(os.getenv('OPENAI_API_KEY'))}
 except Exception:bad('뉴스 MySQL 연결 실패. news:setup 확인이 필요합니다.',503)
@app.get('/regions',dependencies=[Depends(auth)])
def regions():
 with db() as (_,c):return many(c,"SELECT d.id,CONCAT(p.name,' / ',d.name) label FROM districts d JOIN provinces p ON p.id=d.province_id ORDER BY p.name,d.name")
@app.get('/topics',dependencies=[Depends(auth)])
def topics():
 with db() as (_,c):return many(c,"SELECT t.id,t.title,t.category,t.district_id,t.is_demo,t.status,CONCAT(p.name,' / ',d.name) region_name FROM news_topics t JOIN districts d ON d.id=t.district_id JOIN provinces p ON p.id=d.province_id ORDER BY t.id DESC LIMIT 100")
@app.post('/topics',status_code=201,dependencies=[Depends(auth)])
async def new_topic(req:Request):
 x=await req.json();title=str(x.get('title') or '').strip();kind=str(x.get('category') or 'festival')
 if not title or len(title)>200 or kind not in ('festival','tourism','transport','culture','other'):bad('주제·분류 확인 필요',422)
 try:district=int(x.get('district_id'))
 except (ValueError,TypeError):bad('시군구 선택 필요',422)
 with db() as (_,c):
  if not one(c,'SELECT id FROM districts WHERE id=%s',(district,)):bad('지역 없음',404)
  c.execute("INSERT INTO news_topics(district_id,title,category,status,is_demo,created_by) VALUES(%s,%s,%s,'draft',%s,%s)",(district,title,kind,bool(x.get('is_demo',False)),str(req.headers.get('x-news-editor','admin'))[:100]))
  new_id=c.lastrowid
 return {'ok':True,'id':new_id}
@app.get('/topics/{id}/sources',dependencies=[Depends(auth)])
def sources(id:int):
 with db() as (_,c):
  topic(c,id);return many(c,'SELECT id,organization,source_title,source_url,source_kind,published_at,is_demo FROM news_sources WHERE topic_id=%s ORDER BY id',(id,))
@app.post('/topics/{id}/sources',status_code=201,dependencies=[Depends(auth)])
async def new_source(id:int,req:Request):
 x=await req.json();org,title,url=validate_source(x);kind=x.get('source_kind','official')
 if kind not in ('official','public_api','csv','manual','other'):bad('출처 구분 오류',422)
 with db() as (_,c):
  t=topic(c,id)
  try:c.execute("INSERT INTO news_sources(topic_id,source_kind,organization,source_title,source_url,source_url_sha256,is_demo,published_at) VALUES(%s,%s,%s,%s,%s,UNHEX(%s),%s,%s)",
    (id,kind,org,title,url,hashlib.sha256(url.encode()).hexdigest(),bool(t['is_demo']),x.get('published_at') or None))
  except Exception as e:
   if getattr(e,'errno',None)==1062:bad('같은 URL이 존재합니다.',409)
   raise
  new_id=c.lastrowid
 return {'ok':True,'id':new_id}
@app.delete('/topics/{id}/sources/{sid}',dependencies=[Depends(auth)])
def delete_source(id:int,sid:int):
 with db() as (_,c):
  topic(c,id)
  if one(c,'SELECT COUNT(*) n FROM news_fact_evidence WHERE source_id=%s',(sid,))['n']:bad('Fact가 참조 중인 출처입니다.',409)
  c.execute('DELETE FROM news_sources WHERE id=%s AND topic_id=%s',(sid,id))
  if not c.rowcount:bad('없는 출처',404)
 return {'ok':True}
@app.get('/topics/{id}/facts',dependencies=[Depends(auth)])
def facts(id:int):
 with db() as (_,c):
  topic(c,id)
  return many(c,'SELECT f.*, (SELECT COUNT(*) FROM news_fact_evidence e WHERE e.fact_id=f.id) evidence_count FROM news_facts f WHERE f.topic_id=%s ORDER BY f.fact_key',(id,))
@app.post('/topics/{id}/facts',status_code=201,dependencies=[Depends(auth)])
async def new_fact(id:int,req:Request):
 x=await req.json();key,typ,val=validate_fact(x)
 with db() as (_,c):
  topic(c,id)
  try:c.execute("INSERT INTO news_facts(topic_id,fact_key,fact_type,value_text,value_number,unit,event_start,event_end,status) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,'candidate')",
    (id,key,typ,val,x.get('value_number'),x.get('unit') or None,x.get('event_start') or None,x.get('event_end') or None))
  except Exception as e:
   if getattr(e,'errno',None)==1062:bad('중복 Fact Key',409)
   raise
  fid=c.lastrowid
 return {'ok':True,'id':fid,'status':'candidate'}
@app.put('/topics/{id}/facts/{fid}',dependencies=[Depends(auth)])
async def edit_fact(id:int,fid:int,req:Request):
 x=await req.json();key,typ,val=validate_fact(x)
 with db() as (_,c):
  if not one(c,'SELECT id FROM news_facts WHERE id=%s AND topic_id=%s',(fid,id)):bad('없는 Fact',404)
  c.execute("UPDATE news_facts SET fact_key=%s,fact_type=%s,value_text=%s,value_number=%s,unit=%s,event_start=%s,event_end=%s,status='candidate',verification_note=NULL,verified_by=NULL,verified_at=NULL WHERE id=%s AND topic_id=%s",
   (key,typ,val,x.get('value_number'),x.get('unit') or None,x.get('event_start') or None,x.get('event_end') or None,fid,id))
 return {'ok':True,'status':'candidate','message':'수정 후 재검증이 필요합니다.'}
@app.delete('/topics/{id}/facts/{fid}',dependencies=[Depends(auth)])
def delete_fact(id:int,fid:int):
 with db() as (_,c):
  topic(c,id)
  if one(c,'SELECT COUNT(*) n FROM news_claim_facts WHERE fact_id=%s',(fid,))['n']:bad('기사에서 사용한 Fact는 삭제 금지',409)
  c.execute('DELETE FROM news_fact_evidence WHERE fact_id=%s',(fid,))
  c.execute('DELETE FROM news_facts WHERE id=%s AND topic_id=%s',(fid,id))
  if not c.rowcount:bad('없는 Fact',404)
 return {'ok':True}
@app.post('/topics/{id}/facts/{fid}/evidence',dependencies=[Depends(auth)])
async def evidence(id:int,fid:int,req:Request):
 x=await req.json();sid=int(x.get('source_id',0))
 with db() as (_,c):
  if not one(c,'SELECT id FROM news_facts WHERE id=%s AND topic_id=%s',(fid,id)):bad('다른 주제의 Fact',422)
  if not one(c,'SELECT id FROM news_sources WHERE id=%s AND topic_id=%s',(sid,id)):bad('다른 주제의 출처',422)
  c.execute('INSERT INTO news_fact_evidence(fact_id,source_id,excerpt_reference,evidence_note) VALUES(%s,%s,%s,%s) ON DUPLICATE KEY UPDATE excerpt_reference=VALUES(excerpt_reference),evidence_note=VALUES(evidence_note)',
   (fid,sid,str(x.get('excerpt_reference') or '')[:500],str(x.get('evidence_note') or '')[:4000]))
  c.execute("UPDATE news_facts SET status='candidate',verified_by=NULL,verified_at=NULL WHERE id=%s",(fid,))
 return {'ok':True}
@app.post('/topics/{id}/facts/{fid}/verify',dependencies=[Depends(auth)])
async def verify(id:int,fid:int,req:Request):
 x=await req.json()
 with db() as (_,c):
  f=one(c,'SELECT * FROM news_facts WHERE id=%s AND topic_id=%s',(fid,id))
  if not f:bad('Fact 없음',404)
  n=one(c,'SELECT COUNT(*) n FROM news_fact_evidence WHERE fact_id=%s',(fid,))['n']
  can_verify(f,n,x.get('editor_confirmed') is True,x.get('verification_note'))
  c.execute("UPDATE news_facts SET status='verified',verification_note=%s,verified_by=%s,verified_at=NOW() WHERE id=%s",
    (str(x['verification_note'])[:4000],str(req.headers.get('x-news-editor','admin'))[:100],fid))
 return {'ok':True,'status':'verified'}
def approved_facts(c,id):
 return many(c,"SELECT f.* FROM news_facts f WHERE f.topic_id=%s AND f.status='verified' AND EXISTS(SELECT 1 FROM news_fact_evidence e WHERE e.fact_id=f.id) ORDER BY f.fact_key",(id,))
@app.get('/topics/{id}/fact-sheet',dependencies=[Depends(auth)])
def sheet(id:int):
 with db() as (_,c):
  t=topic(c,id);rows=approved_facts(c,id)
  count=one(c,"SELECT COUNT(*) n FROM news_facts WHERE topic_id=%s AND status<>'verified'",(id,))['n']
 return {'topic_id':id,'title':t['title'],'region':t['region_name'],'verified_facts':rows,'unverified_count':count,'snapshot':fingerprint(rows),'is_demo':bool(t['is_demo'])}
@app.post('/topics/{id}/generate',dependencies=[Depends(auth)])
def generate(id:int,req:Request):
 with db() as (_,c):
  t=topic(c,id);rows=approved_facts(c,id)
 if not rows:bad('검증 Fact가 없습니다.',409)
 if len(rows)>40:bad('Fact는 최대 40건입니다.',422)
 snap=fingerprint(rows)
 try:article,usage=generate_article(t,rows)
 except RuntimeError as e:bad(str(e),503)
 except ValueError as e:bad(str(e),422)
 except Exception as e:raise HTTPException(502,detail='OpenAI API 오류: 잔액·키·모델 확인') from e
 with db() as (_,c):
  c.execute('SELECT id FROM news_topics WHERE id=%s FOR UPDATE',(id,));c.fetchone()
  latest=approved_facts(c,id)
  if fingerprint(latest)!=snap:bad('생성 중 Fact 변경됨. 다시 생성하세요.',409)
  rev=one(c,'SELECT COALESCE(MAX(revision_no),0)+1 n FROM news_drafts WHERE topic_id=%s',(id,))['n']
  c.execute("INSERT INTO news_drafts(topic_id,revision_no,title,body_text,model_name,fact_snapshot_sha256,status,is_demo,created_by) VALUES(%s,%s,%s,%s,%s,%s,'generated',%s,%s)",
     (id,rev,article['title'],article['body'],usage['model'],snap,bool(t['is_demo']),str(req.headers.get('x-news-editor','admin'))[:100]))
  draft_id=c.lastrowid;keys={f['fact_key']:f['id'] for f in latest}
  for i,cl in enumerate(article['claims'],1):
   c.execute("INSERT INTO news_claims(draft_id,sequence_no,statement_text,status) VALUES(%s,%s,%s,'unverified')",(draft_id,i,str(cl['sentence'])[:6000]))
   cid=c.lastrowid
   for k in set(cl['fact_keys']):c.execute('INSERT INTO news_claim_facts(claim_id,fact_id) VALUES(%s,%s)',(cid,keys[k]))
  c.execute("INSERT INTO news_ai_usage(topic_id,draft_id,model_name,provider_request_id,input_tokens,output_tokens,cached_input_tokens,status) VALUES(%s,%s,%s,%s,%s,%s,%s,'success')",
   (id,draft_id,usage['model'],usage['request_id'],usage['input_tokens'],usage['output_tokens'],usage['cached_input_tokens']))
 return {'ok':True,'draft_id':draft_id,'revision_no':rev,'title':article['title'],'body':article['body'],'status':'generated',
  'claims_review_required':len(article['claims']),'fact_snapshot':snap,'usage':usage,'message':'초안 저장 OK — 관리자 승인 및 사용자 공개는 V8.5.2에서 연결'}
@app.get('/topics/{id}/drafts',dependencies=[Depends(auth)])
def drafts(id:int):
 with db() as (_,c):
  topic(c,id);return many(c,'SELECT id,revision_no,title,body_text,status,model_name,fact_snapshot_sha256,created_at FROM news_drafts WHERE topic_id=%s ORDER BY revision_no DESC',(id,))
@app.get('/drafts/{id}',dependencies=[Depends(auth)])
def draft(id:int):
 with db() as (_,c):
  d=one(c,'SELECT * FROM news_drafts WHERE id=%s',(id,))
  if not d:bad('기사 없음',404)
  claims=many(c,'SELECT x.id,x.sequence_no,x.statement_text,x.status,GROUP_CONCAT(f.fact_key) fact_keys FROM news_claims x LEFT JOIN news_claim_facts m ON m.claim_id=x.id LEFT JOIN news_facts f ON f.id=m.fact_id WHERE x.draft_id=%s GROUP BY x.id ORDER BY x.sequence_no',(id,))
 return {'draft':d,'claims':claims,'approval_enabled':False,'message':'V8.5.1은 초안 검토 단계입니다. 사용자 게시 없음.'}
