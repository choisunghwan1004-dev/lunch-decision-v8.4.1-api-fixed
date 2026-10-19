"""V8.5.1 real DB+OpenAI integration smoke test. Paid call ONLY with --run-live."""
import os,sys,uuid,json
from pathlib import Path
from datetime import datetime
import httpx
from dotenv import load_dotenv
ROOT=Path(__file__).resolve().parents[2]
load_dotenv(ROOT/'.env')
REPORT=ROOT/'diagnostics/news-real-test.json'
def main():
 if '--run-live' not in sys.argv:
  print('SKIPPED: --run-live 필수');return 2
 missing=[x for x in ('DB_PASSWORD','OPENAI_API_KEY','NEWS_INTERNAL_TOKEN') if not os.getenv(x)]
 if missing:
  print('SKIPPED: 환경변수 없음:',', '.join(missing));return 2
 if len(os.environ['NEWS_INTERNAL_TOKEN'])!=64:
  print('SKIPPED: NEWS_INTERNAL_TOKEN은 64자리 hex여야 합니다.');return 2
 out={'executed_at':datetime.now().isoformat(),'phase':'started','real_db':False,'real_openai':False}
 REPORT.parent.mkdir(exist_ok=True)
 try:
  with httpx.Client(base_url='http://127.0.0.1:8001',timeout=60,headers={'X-News-Internal-Token':os.environ['NEWS_INTERNAL_TOKEN'],'X-News-Editor':'synthetic-test'}) as c:
   def do(method,url,body=None):
    r=c.request(method,url,json=body)
    if r.status_code>=400:raise RuntimeError(method+' '+url+' HTTP '+str(r.status_code)+': '+r.text[:200])
    return r.json()
   assert do('GET','/health')['ok']
   region=next((r for r in do('GET','/regions') if '종로구' in r['label'] and '서울' in r['label']),None)
   if not region:raise RuntimeError('종로구 DB 데이터 없음 (npm run seed:demo)')
   suffix=uuid.uuid4().hex[:12]
   t=do('POST','/topics',{'district_id':region['id'],'title':'[수업용 가상] 종로구 실통합 테스트 '+suffix,'category':'festival','is_demo':True})
   tid=t['id'];out['topic_id']=tid
   src=do('POST','/topics/'+str(tid)+'/sources',{'organization':'자동테스트용 가상자료','source_kind':'manual','source_title':'실존 행사 아님 — 합성 테스트','source_url':'https://example.org/v851-synthetic/'+suffix})
   f=do('POST','/topics/'+str(tid)+'/facts',{'fact_key':'F01','fact_type':'text','value_text':'[수업용 가상 데이터] 종로구의 가상 행사는 10월 24일이라고 가정한다. 실제 행사가 아니다.'})
   fid=f['id'];out['real_db']=True
   do('POST','/topics/'+str(tid)+'/facts/'+str(fid)+'/evidence',{'source_id':src['id'],'evidence_note':'TEST ONLY: 가상 자료'})
   do('POST','/topics/'+str(tid)+'/facts/'+str(fid)+'/verify',{'editor_confirmed':True,'verification_note':'합성 테스트 fixture 일치, 실제 기사 사용 금지'})
   sheet=do('GET','/topics/'+str(tid)+'/fact-sheet');assert len(sheet['verified_facts'])==1
   draft=do('POST','/topics/'+str(tid)+'/generate',{});assert draft['status']=='generated'
   out.update({'real_openai':True,'phase':'passed','draft_id':draft['draft_id'],'request_id':draft['usage']['request_id']})
 except Exception as e:out.update({'phase':'failed','error':str(e)[:500]})
 REPORT.write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
 print(json.dumps(out,ensure_ascii=False,indent=2))
 return 0 if out['phase']=='passed' else 1
if __name__=='__main__':sys.exit(main())
