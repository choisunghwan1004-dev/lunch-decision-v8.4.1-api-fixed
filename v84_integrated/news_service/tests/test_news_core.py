from types import SimpleNamespace
import json,pytest
from fastapi.testclient import TestClient
from news_service.validation import validate_source,validate_fact,can_verify,fingerprint,parse_draft
from news_service.article_ai import generate_article
from news_service.app import app
SAMPLE={'fact_key':'F01','fact_type':'text','value_text':'[수업용 가상 데이터] 종로구의 가상 문화행사 날짜는 10월 24일이라는 테스트 가정','value_number':None}
def test_https_only():
 with pytest.raises(ValueError):validate_source({'organization':'기관','source_title':'제목','source_url':'http://example.org'})
def test_valid_https():
 assert validate_source({'organization':'기관','source_title':'제목','source_url':'https://example.org/test'})[0]=='기관'
def test_fact_type():
 with pytest.raises(ValueError):validate_fact({**SAMPLE,'fact_type':'unknown'})
def test_number():
 with pytest.raises(ValueError):validate_fact({**SAMPLE,'fact_type':'number'})
def test_date_order():
 with pytest.raises(ValueError):validate_fact({**SAMPLE,'event_start':'2026-10-20','event_end':'2026-10-19'})
def test_source_link_required():
 with pytest.raises(ValueError):can_verify(SAMPLE,0,True,'checked')
def test_human_confirmation_required():
 with pytest.raises(ValueError):can_verify(SAMPLE,1,False,'checked')
def test_verification_valid():
 assert can_verify(SAMPLE,1,True,'실제 원문 대조')
def test_snapshot_changes():
 assert fingerprint([SAMPLE])!=fingerprint([{**SAMPLE,'value_text':'변경됨'}])
def test_snapshot_order():
 assert fingerprint([SAMPLE,{**SAMPLE,'fact_key':'F02'}])==fingerprint([{**SAMPLE,'fact_key':'F02'},SAMPLE])
def test_unknown_fact_rejected():
 d={'title':'종로구 행사 정보 기사','body':'수업용 가상 자료라고 가정하는 테스트 안내문입니다. '*3,'claims':[{'sentence':'문장','fact_keys':['NOT_VERIFIED']}]}
 with pytest.raises(ValueError):parse_draft(json.dumps(d,ensure_ascii=False),{'F01'})
def test_fake_openai_call():
 d={'title':'종로구 가상 행사 안내','body':'수업용 가상 데이터입니다. 가상의 행사는 실제 행사가 아닙니다. '*3,'claims':[{'sentence':'행사 안내','fact_keys':['F01']}]}
 call={}
 class Responses:
  def create(self,**kw):
   call.update(kw)
   return SimpleNamespace(id='resp_test',output_text=json.dumps(d,ensure_ascii=False),
    usage=SimpleNamespace(input_tokens=102,output_tokens=89,input_tokens_details=SimpleNamespace(cached_tokens=0)))
 data,usage=generate_article({'region_name':'서울 종로구','title':'지역 축제','category':'festival','is_demo':True},[SAMPLE],client=SimpleNamespace(responses=Responses()))
 assert call['model']=='gpt-4.1-mini' and call['store'] is False and usage['input_tokens']==102
 assert data['claims'][0]['fact_keys']==['F01']
def test_auth_without_token(monkeypatch):
 monkeypatch.setenv('NEWS_INTERNAL_TOKEN','a'*64)
 assert TestClient(app).get('/health').status_code==403
def test_auth_wrong_token(monkeypatch):
 monkeypatch.setenv('NEWS_INTERNAL_TOKEN','a'*64)
 assert TestClient(app).get('/health',headers={'X-News-Internal-Token':'b'*64}).status_code==403
