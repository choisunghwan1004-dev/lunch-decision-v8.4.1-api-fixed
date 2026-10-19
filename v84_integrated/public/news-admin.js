/* V8.5.1 admin: existing session, no API secret in browser */
(()=>{
const $=id=>document.getElementById(id);let started=false,sources=[],facts=[];
async function request(url,method='GET',body){
 const opt={method,headers:{}};if(body!==undefined){opt.headers['Content-Type']='application/json';opt.body=JSON.stringify(body)}
 const response=await fetch('/api/news'+url,opt);const d=await response.json().catch(()=>({message:'응답 오류'}));
 if(!response.ok)throw Error(d.message||d.detail||'HTTP 오류');return d;
}
function status(msg,error=false){$('nStatus').textContent=msg;$('nStatus').className='status '+(error?'error':'ok')}
function element(tag,s){const e=document.createElement(tag);e.textContent=String(s||'');return e}
function addOption(s,id,label){let e=document.createElement('option');e.value=String(id);e.textContent=label;s.append(e)}
function button(label,cb){let e=element('button',label);e.type='button';e.addEventListener('click',()=>cb().catch(x=>status(x.message,true)));return e}
const topic=()=>Number($('nTopic').value);
async function reloadTopics(id){
 const arr=await request('/topics'),s=$('nTopic');s.replaceChildren();addOption(s,'','주제 선택');
 arr.forEach(x=>addOption(s,x.id,x.region_name+' · '+x.title+(x.is_demo?' (가상)':'')));
 if(id)s.value=String(id);if(!s.value&&arr.length)s.value=String(arr[0].id);await reload();
}
async function reload(){
 const id=topic();if(!id)return;
 [sources,facts]=await Promise.all([request('/topics/'+id+'/sources'),request('/topics/'+id+'/facts')]);
 const div=$('nSources');div.replaceChildren();div.append(element('h4','출처 '+sources.length+'건'));
 for(const src of sources){
  const row=element('div',src.organization+' · '+src.source_title+' — '+src.source_url);row.className='news-row';
  row.append(button('삭제',async()=>{if(!confirm('출처 삭제?'))return;await request('/topics/'+id+'/sources/'+src.id,'DELETE');await reload()}));div.append(row)
 }
 const out=$('nFacts');out.replaceChildren();out.append(element('h4','Fact '+facts.length+'건'));
 for(const f of facts){
  let row=element('div',f.fact_key+' ['+f.status+'] (근거 '+f.evidence_count+'건): '+f.value_text);row.className='news-row';
  let pick=document.createElement('select');addOption(pick,'','출처 선택');
  sources.forEach(x=>addOption(pick,x.id,x.organization+' / '+x.source_title));row.append(pick);
  row.append(button('근거 연결',async()=>{if(!pick.value)throw Error('출처 선택 필요');await request('/topics/'+id+'/facts/'+f.id+'/evidence','POST',{source_id:Number(pick.value),evidence_note:'원문 대조 예정'});await reload()}));
  row.append(button('원문 대조 후 검증',async()=>{let note=prompt('원문에서 직접 확인한 위치·의견');if(!note||!confirm('실제 출처 문서를 직접 대조했습니까?'))return;await request('/topics/'+id+'/facts/'+f.id+'/verify','POST',{editor_confirmed:true,verification_note:note});await reload()}));
  row.append(button('삭제',async()=>{if(!confirm('Fact 삭제?'))return;await request('/topics/'+id+'/facts/'+f.id,'DELETE');await reload()}));out.append(row)
 }
 await loadDrafts();
}
async function loadDrafts(){
 const id=topic();if(!id)return;const rows=await request('/topics/'+id+'/drafts');let div=$('nDrafts');div.replaceChildren();
 rows.forEach(x=>{let row=element('div','v'+x.revision_no+' · '+x.title+' ['+x.status+']');row.className='news-row';
 row.append(button('초안 보기',async()=>{$('nDraftOutput').textContent=JSON.stringify(await request('/drafts/'+x.id),null,2)}));div.append(row)})
}
async function init(){if(started)return;started=true;try{
 const [h,regions]=await Promise.all([request('/health'),request('/regions')]);let sel=$('nDistrict');sel.replaceChildren();addOption(sel,'','시군구 선택');
 regions.forEach(x=>addOption(sel,x.id,x.label));let j=regions.find(x=>x.label.includes('서울')&&x.label.includes('종로구'));if(j)sel.value=String(j.id);
 await reloadTopics();status('뉴스 DB 연결 OK / OpenAI '+(h.openaiConfigured?'키 설정됨':'키 미설정'));
 }catch(e){started=false;status(e.message,true)}
}
function bind(id,fn){$(id).addEventListener('click',()=>fn().catch(e=>status(e.message,true)))}
bind('nAddTopic',async()=>{const x=await request('/topics','POST',{district_id:Number($('nDistrict').value),title:$('nTitle').value,category:$('nCategory').value,is_demo:$('nDemo').checked});await reloadTopics(x.id);status('뉴스 주제 등록 OK')});
bind('nAddSource',async()=>{if(!topic())throw Error('주제를 먼저 선택하세요');await request('/topics/'+topic()+'/sources','POST',{organization:$('nOrganization').value,source_title:$('nSourceTitle').value,source_url:$('nSourceUrl').value,source_kind:$('nSourceKind').value});await reload();status('원자료 등록 OK')});
bind('nAddFact',async()=>{if(!topic())throw Error('주제를 먼저 선택하세요');const n=$('nFactNumber').value;await request('/topics/'+topic()+'/facts','POST',{fact_key:$('nFactKey').value,fact_type:$('nFactType').value,value_text:$('nFactValue').value,value_number:n?Number(n):null,unit:$('nFactUnit').value});await reload();status('Fact 등록 OK / 검증 전')});
bind('nLoadSheet',async()=>{let d=await request('/topics/'+topic()+'/fact-sheet');$('nSheet').textContent=JSON.stringify(d,null,2);status('검증 '+d.verified_facts.length+'건 / 미검증 '+d.unverified_count+'건')});
bind('nReloadDrafts',loadDrafts);
bind('nGenerate',async()=>{status('OpenAI 초안 생성 중...');let d=await request('/topics/'+topic()+'/generate','POST',{});$('nDraftOutput').textContent=d.title+'\n\n'+d.body+'\n\n'+d.message;await loadDrafts();status(d.message)});
$('nTopic').addEventListener('change',()=>reload().catch(e=>status(e.message,true)));
window.newsAdminInit=init;
})();