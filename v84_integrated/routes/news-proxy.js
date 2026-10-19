const express=require('express');const router=express.Router();
router.use((req,res,next)=>{
 if(!req.session?.adminId)return res.status(401).json({message:'관리자 로그인이 필요합니다.'});
 if(!['GET','POST','PUT','DELETE'].includes(req.method))return res.status(405).json({message:'지원하지 않는 요청'});
 const key=process.env.NEWS_INTERNAL_TOKEN||'';
 if(!/^[a-f0-9]{64}$/i.test(key))return res.status(503).json({message:'NEWS_INTERNAL_TOKEN 64자리 hex 설정이 필요합니다.'});
 if(req.method!=='GET'){
  const origin=req.get('origin'),expected=req.protocol+'://'+req.get('host');
  if(origin&&origin!==expected)return res.status(403).json({message:'외부 사이트의 쓰기 요청이 차단되었습니다.'});
  if(req.get('content-type')?.split(';')[0]!=='application/json')return res.status(415).json({message:'JSON만 허용'});
 }
 next();
});
router.use(async(req,res)=>{
 try{
  const query=new URLSearchParams(req.query).toString();
  const url='http://127.0.0.1:8001'+req.path+(query?'?'+query:'');
  const cfg={method:req.method,signal:AbortSignal.timeout(45000),headers:{
   'X-News-Internal-Token':process.env.NEWS_INTERNAL_TOKEN,
   'X-News-Editor':String(req.session.adminUsername||'admin').slice(0,100)}};
  if(req.method!=='GET'){cfg.headers['Content-Type']='application/json';cfg.body=JSON.stringify(req.body||{})}
  const upstream=await fetch(url,cfg);let body;try{body=await upstream.json()}catch{body={message:'뉴스 서버 응답 오류'}}
  if(!upstream.ok)return res.status(upstream.status).json({ok:false,message:typeof body.detail==='string'?body.detail:body.message||'뉴스 서버 오류'});
  return res.status(upstream.status).json(body);
 }catch(e){return res.status(503).json({ok:false,message:e.name==='TimeoutError'?'뉴스 생성 제한시간 초과':'내부 뉴스 서버 실행 상태를 확인하세요. (run_news.bat)'})}
});
module.exports=router;
