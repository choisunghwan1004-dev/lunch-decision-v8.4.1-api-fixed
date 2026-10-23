import hashlib,json
def validate_fact(f,sources):
 errors=[]
 if not str(f.get('value_text','')).strip():errors.append('내용 누락')
 if f.get('source_id') not in sources:errors.append('출처 없음')
 else:
  s=sources[f['source_id']]
  if not(s.get('organization') and s.get('source_url') and s.get('published_at')):errors.append('출처 메타정보 누락')
 if f.get('fact_type')=='number' and f.get('value_number') is None:errors.append('수치 없음')
 return errors
def allowed_to_generate(facts):
 return bool(facts) and all(f.get('status')=='verified' and f.get('source_id') for f in facts)
def review_result(checks):
 return all(checks.get(k) is True for k in ('numbers','time_and_region','no_unfounded_causes','source_and_observed_at'))
def fact_hash(facts):
 return hashlib.sha256(json.dumps(facts,sort_keys=True,ensure_ascii=False,default=str).encode()).hexdigest()
def news_prompt(topic,facts):
 if not allowed_to_generate(facts):raise ValueError('검증된 Fact 필요')
 return '다음 근거 외의 사실, 날짜, 인과관계를 생성하지 말 것. 제목 25자 이내, 본문 500자 이내, 출처와 날짜 표시.\n'+json.dumps({'topic':topic,'facts':facts},ensure_ascii=False,default=str)
