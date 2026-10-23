import os,datetime,secrets
from pathlib import Path
from fastapi import FastAPI,Depends,HTTPException
from fastapi.responses import FileResponse
from fastapi.security import HTTPBasic,HTTPBasicCredentials
from pydantic import BaseModel
from db import db,read
from logic import validate_fact,allowed_to_generate,review_result,fact_hash,news_prompt
app=FastAPI(title='V8.5.1 AI 지역 뉴스')
auth=HTTPBasic()
def admin(c:HTTPBasicCredentials=Depends(auth)):
 name=os.getenv('NEWS_ADMIN_USERNAME','admin');pw=os.getenv('NEWS_ADMIN_PASSWORD','')
 if not pw or not(secrets.compare_digest(c.username,name) and secrets.compare_digest(c.password,pw)):raise HTTPException(401,'관리자 인증 오류',headers={'WWW-Authenticate':'Basic'})
 return name
class Topic(BaseModel):
 district_id:int;title:str;category:str='festival'
class Source(BaseModel):
 topic_id:int;organization:str;source_title:str;source_url:str;published_at:datetime.datetime
class Fact(BaseModel):
 topic_id:int;fact_key:str;fact_type:str='text';value_text:str;source_id:int;value_number:float|None=None
class FactEdit(BaseModel):
 value_text:str;value_number:float|None=None
class Check(BaseModel):
 numbers:bool;time_and_region:bool;no_unfounded_causes:bool;source_and_observed_at:bool;comment:str=''
@app.get('/')
def home(_=Depends(admin)):return FileResponse(Path(__file__).parent/'static/index.html')
@app.get('/health')
def health():return {'ok':True,'version':'8.5.1'}
@app.get('/topics')
def topics(_=Depends(admin)):return read('SELECT * FROM news_topics ORDER BY id DESC')
@app.post('/topics',status_code=201)
def topic(t:Topic,_=Depends(admin)):
 with db() as c:
  c.execute('SELECT id FROM districts WHERE id=%s',(t.district_id,))
  if not c.fetchone():raise HTTPException(422,'지역 ID 없음')
  c.execute('INSERT INTO news_topics(district_id,title,category,created_by) VALUES(%s,%s,%s,%s)',(t.district_id,t.title,t.category,_));return {'id':c.lastrowid}
@app.post('/sources',status_code=201)
def source(t:Source,_=Depends(admin)):
 if not t.source_url.startswith(('https://','http://')):raise HTTPException(422,'출처 URL 필요')
 with db() as c:
  c.execute('INSERT INTO news_sources(topic_id,organization,source_title,source_url,published_at) VALUES(%s,%s,%s,%s,%s)',(t.topic_id,t.organization,t.source_title,t.source_url,t.published_at));return {'id':c.lastrowid}
@app.get('/sources/{topic_id}')
def sources(topic_id:int,_=Depends(admin)):return read('SELECT * FROM news_sources WHERE topic_id=%s',(topic_id,))
@app.post('/facts',status_code=201)
def fact(t:Fact,_=Depends(admin)):
 src=read('SELECT * FROM news_sources WHERE id=%s AND topic_id=%s',(t.source_id,t.topic_id))
 errors=validate_fact(t.model_dump(),{t.source_id:src[0]} if src else {})
 if errors:raise HTTPException(422,errors)
 with db() as c:
  c.execute('INSERT INTO news_facts(topic_id,fact_key,fact_type,value_text,value_number) VALUES(%s,%s,%s,%s,%s)',(t.topic_id,t.fact_key,t.fact_type,t.value_text,t.value_number));fid=c.lastrowid
  c.execute('INSERT INTO news_fact_evidence(fact_id,source_id) VALUES(%s,%s)',(fid,t.source_id));return {'id':fid,'status':'candidate'}
@app.get('/facts/{topic_id}')
def facts(topic_id:int,_=Depends(admin)):
 return read('SELECT f.*,e.source_id,s.organization,s.source_url,s.published_at FROM news_facts f JOIN news_fact_evidence e ON e.fact_id=f.id JOIN news_sources s ON s.id=e.source_id WHERE f.topic_id=%s',(topic_id,))
@app.put('/facts/{fact_id}')
def edit(fact_id:int,t:FactEdit,_=Depends(admin)):
 with db() as c:
  c.execute("UPDATE news_facts SET value_text=%s,value_number=%s,status='candidate',verified_by=NULL,verified_at=NULL WHERE id=%s",(t.value_text,t.value_number,fact_id))
  if not c.rowcount:raise HTTPException(404,'Fact 없음')
 return {'status':'candidate'}
@app.delete('/facts/{fact_id}')
def remove(fact_id:int,_=Depends(admin)):
 with db() as c:
  c.execute('DELETE FROM news_fact_evidence WHERE fact_id=%s',(fact_id,))
  c.execute('DELETE FROM news_facts WHERE id=%s',(fact_id,))
  if not c.rowcount:raise HTTPException(404,'Fact 없음')
 return {'ok':True}
@app.post('/facts/{fact_id}/verify')
def verify(fact_id:int,_=Depends(admin)):
 fs=read('SELECT f.*,e.source_id,s.organization,s.source_url,s.published_at FROM news_facts f JOIN news_fact_evidence e ON e.fact_id=f.id JOIN news_sources s ON s.id=e.source_id WHERE f.id=%s',(fact_id,))
 if not fs:raise HTTPException(422,'근거 없음')
 f=fs[0]; errors=validate_fact(f,{f['source_id']:f})
 if errors:raise HTTPException(422,errors)
 with db() as c:c.execute("UPDATE news_facts SET status='verified',verified_by=%s,verified_at=NOW() WHERE id=%s",(_,fact_id))
 return {'status':'verified'}
@app.post('/drafts/{topic_id}/generate')
def generate(topic_id:int,_=Depends(admin)):
 topics=read('SELECT * FROM news_topics WHERE id=%s',(topic_id,))
 if not topics:raise HTTPException(404,'주제 없음')
 facts=read("SELECT f.fact_key,f.fact_type,f.value_text,f.status,e.source_id,s.source_url,s.organization,s.published_at FROM news_facts f JOIN news_fact_evidence e ON e.fact_id=f.id JOIN news_sources s ON s.id=e.source_id WHERE f.topic_id=%s AND f.status='verified'",(topic_id,))
 if not allowed_to_generate(facts):raise HTTPException(422,'검증된 Fact가 없습니다')
 if not os.getenv('OPENAI_API_KEY'):raise HTTPException(503,'OPENAI_API_KEY 미설정')
 from openai import OpenAI
 try:r=OpenAI(api_key=os.environ['OPENAI_API_KEY'],timeout=25).responses.create(model=os.getenv('OPENAI_MODEL','gpt-4.1-mini'),input=news_prompt(topics[0]['title'],facts),max_output_tokens=750)
 except Exception as e:raise HTTPException(502,'모델 통신 실패: '+type(e).__name__)
 body=r.output_text.strip()
 if not body:raise HTTPException(502,'기사 본문 없음')
 with db() as c:
  c.execute('INSERT INTO news_drafts(topic_id,title,body_text,model_name,fact_snapshot_sha256,created_by) VALUES(%s,%s,%s,%s,%s,%s)',(topic_id,body.splitlines()[0][:300],body,os.getenv('OPENAI_MODEL','gpt-4.1-mini'),fact_hash(facts),_))
  return {'draft_id':c.lastrowid,'status':'generated','title':body.splitlines()[0],'body':body}
@app.get('/drafts/{topic_id}')
def drafts(topic_id:int,_=Depends(admin)):return read('SELECT * FROM news_drafts WHERE topic_id=%s ORDER BY id DESC',(topic_id,))
@app.post('/drafts/{draft_id}/review')
def review(draft_id:int,t:Check,_=Depends(admin)):
 passed=review_result(t.model_dump())
 with db() as c:
  c.execute('SELECT id FROM news_drafts WHERE id=%s',(draft_id,))
  if not c.fetchone():raise HTTPException(404,'초안 없음')
  c.execute('INSERT INTO news_reviews(draft_id,reviewer_key,check_passed,comment) VALUES(%s,%s,%s,%s)',(draft_id,_,passed,t.comment))
  c.execute('UPDATE news_drafts SET status=%s WHERE id=%s',('in_review' if passed else 'changes_requested',draft_id))
 return {'check_passed':passed,'approval_enabled':False}
@app.post('/drafts/{draft_id}/approve')
def blocked(draft_id:int,_=Depends(admin)):raise HTTPException(409,'V8.5.1에서는 최종 승인/게시 미구현')
