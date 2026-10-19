const express=require('express'),bcrypt=require('bcryptjs'),crypto=require('node:crypto');
const db=require('../db'),{loadTree,sourceLevel,virtual}=require('../lib/tree'),{between}=require('../lib/route');
const {handler:wrap,bad,validId,safeText}=require('../lib/errors');
const router=express.Router();
const pool=()=>db.getPool();
const query=async(sql,params=[])=>(await pool().query(sql,params))[0];
const one=async(sql,args=[])=> (await query(sql,args))[0]||null;
function needAdmin(req,res,next){if(!req.session.adminId)return res.status(401).json({message:'관리자 로그인이 필요합니다.'});next();}
function needUser(req,res,next){if(!req.session.userId)return res.status(401).json({message:'회원 로그인이 필요합니다.'});next();}
function numberIn(x,min,max,label){const n=Number(x);if(!Number.isFinite(n)||n<min||n>max)throw bad(`${label}: ${min}~${max} 범위를 입력하세요.`);return n;}
const encode=(r)=>({id:Number(r.id),name:r.name,category:r.category||'기타',city_name:r.city_name,region_name:r.region_name,country_name:r.country_name,area_name:r.area_name,price_min:r.price_min??0,price_max:r.price_max??0,address:r.address||'',main_menu:r.main_menu||r.category||'',latitude:r.latitude==null?null:Number(r.latitude),longitude:r.longitude==null?null:Number(r.longitude),rating:r.rating==null?null:Number(r.rating),review_count:r.review_count||0,image_path:r.image_path||null,lunch_start:r.lunch_start||'11:00:00',lunch_end:r.lunch_end||'15:00:00',place_type:r.place_type,is_demo:!!r.is_demo,meal_minutes:60,country_code:r.country_code||'KR',phone:r.phone||null});

// Administrator: no DDL, no default user inserted on login.
router.post('/auth/login',wrap(async(req,res)=>{
 const username=safeText(req.body.username,80),password=String(req.body.password??'');
 const admin=process.env.ADMIN_USERNAME||'admin',pass=process.env.ADMIN_PASSWORD;
 if(!pass||pass==='CHANGE_ME_BEFORE_USE')throw bad('먼저 .env에서 ADMIN_PASSWORD를 설정하세요.',503);
 const same=(x,y)=>{const a=crypto.createHash('sha256').update(x).digest(),b=crypto.createHash('sha256').update(y).digest();return crypto.timingSafeEqual(a,b)};
 if(!same(username,admin)||!same(password,pass))throw bad('아이디 또는 비밀번호를 확인하세요.',401);
 await new Promise((resolve,reject)=>req.session.regenerate(e=>e?reject(e):resolve()));
 req.session.adminId='env';req.session.adminUsername=username;
 await new Promise((resolve,reject)=>req.session.save(e=>e?reject(e):resolve()));
 res.json({ok:true,message:'관리자 로그인 OK'});
}));
router.get('/auth/me',(req,res)=>res.json({loggedIn:!!req.session.adminId,username:req.session.adminUsername||null}));
router.post('/auth/logout',(req,res)=>req.session.destroy(()=>res.json({ok:true})));

router.get('/context/locations',wrap(async(req,res)=>res.json(await loadTree(pool()))));
router.get('/admin/locations/tree',needAdmin,wrap(async(req,res)=>res.json(await loadTree(pool()))));
router.get('/admin/dashboard',needAdmin,wrap(async(req,res)=>{
 const keys={countries:'countries',regions:'provinces',cities:'districts',towns:'admin_towns',areas:'commercial_areas',restaurants:'places',users:'users'};
 const x={};for(const [alias,t] of Object.entries(keys)){
  const sql=t==='places' ? "SELECT COUNT(*) n FROM places WHERE place_type='restaurant'" : `SELECT COUNT(*) n FROM ${t}`;
  x[alias]=Number((await one(sql)).n);
 }
 x.places=Number((await one("SELECT COUNT(*) n FROM places WHERE place_type<>'restaurant'")).n);
 x.locations=x.countries+x.regions+x.cities+x.towns+Number((await one('SELECT COUNT(*) n FROM town_legal_links')).n)+x.areas;
 res.json(x);
}));
router.get('/admin/cities',needAdmin,wrap(async(req,res)=>res.json(await query('SELECT id,name FROM districts ORDER BY name'))));
const fullSql=`SELECT p.*,a.name area_name,t.name town_name,d.id district_id,d.name city_name,pr.name region_name,c.name country_name,c.code country_code
 FROM places p JOIN commercial_areas a ON a.id=p.area_id JOIN admin_towns t ON t.id=a.town_id JOIN districts d ON d.id=t.district_id JOIN provinces pr ON pr.id=d.province_id JOIN countries c ON c.id=pr.country_id`;
router.get('/admin/restaurants',needAdmin,wrap(async(req,res)=>res.json((await query(fullSql+" WHERE p.place_type='restaurant' ORDER BY p.id DESC LIMIT 500")).map(encode))));
router.get('/admin/places',needAdmin,wrap(async(req,res)=>res.json((await query(fullSql+" WHERE p.place_type<>'restaurant' ORDER BY p.id DESC LIMIT 500")).map(encode))));
router.get('/admin/locations/diagnostics',needAdmin,wrap(async(req,res)=>{
 const checks={
  districts_without_province:'SELECT COUNT(*) n FROM districts d LEFT JOIN provinces p ON p.id=d.province_id WHERE p.id IS NULL',
  towns_without_district:'SELECT COUNT(*) n FROM admin_towns t LEFT JOIN districts d ON d.id=t.district_id WHERE d.id IS NULL',
  areas_without_town:'SELECT COUNT(*) n FROM commercial_areas a LEFT JOIN admin_towns t ON t.id=a.town_id WHERE t.id IS NULL',
  invalid_town_legal:'SELECT COUNT(*) n FROM town_legal_links l JOIN admin_towns t ON t.id=l.town_id JOIN legal_units u ON u.id=l.legal_unit_id WHERE t.district_id<>u.district_id OR l.district_id<>t.district_id',
  areas_without_places:'SELECT COUNT(*) n FROM commercial_areas a LEFT JOIN places p ON p.area_id=a.id WHERE p.id IS NULL'
 };
 const result={ok:true,foreignKeys:{},emptyAreas:0};
 for(const [key,sql]of Object.entries(checks)){const n=Number((await one(sql)).n);if(key==='areas_without_places')result.emptyAreas=n;else {result.foreignKeys[key]=n;if(n)result.ok=false}}
 const townsWithoutArea=Number((await one('SELECT COUNT(*) n FROM admin_towns t LEFT JOIN commercial_areas a ON a.town_id=t.id WHERE a.id IS NULL')).n);
 result.townsWithoutCommercialArea=townsWithoutArea;
 result.note='읍·면·동이 있어도 상권이 없을 수 있습니다. DB FK 오류와 데이터 부족을 구분해 표시합니다.';
 res.json(result);
}));
router.post('/admin/locations',needAdmin,wrap(async(req,res)=>{
 const level=safeText(req.body.level,12),name=safeText(req.body.name,150),virtualParent=req.body.parent_id;
 if(!name)throw bad('지역명을 입력하세요.');
 if(!['country','province','district','town','ri','area'].includes(level))throw bad('지원되지 않는 지역 단계');
 const tree=await loadTree(pool());const p=tree.find(x=>x.id===Number(virtualParent));
 const parents={province:['country'],district:['province'],town:['district'],ri:['town'],area:['town','ri']};
 if(level!=='country'&&!parents[level]?.includes(p?.level))throw bad('상위 지역이 올바르지 않습니다. 읍·면·동을 먼저 선택하세요.');
 const code=level==='country'?safeText(req.body.code,8).toUpperCase():'USR-'+level.toUpperCase()+'-'+crypto.randomBytes(8).toString('hex');
 if(level==='country'&&!/^[A-Z]{2,3}$/.test(code))throw bad('국가 코드는 영문 2~3자리입니다.');
 const data={country:{table:'countries',fk:'',extra:{currency:level==='country'?(code==='JP'?'JPY':'KRW'):undefined}},province:{table:'provinces',fk:'country_id'},district:{table:'districts',fk:'province_id'},town:{table:'admin_towns',fk:'district_id'},ri:{table:'legal_units',fk:'district_id'},area:{table:'commercial_areas',fk:'town_id'}}[level];
 const c=await pool().getConnection();
 try{
  await c.beginTransaction();
  const entries={code,name};
  if(level==='country')entries.currency=code==='JP'?'JPY':'KRW';
  else if(level==='ri'){
   const town=await (async()=>{const [[row]]=await c.query('SELECT district_id FROM admin_towns WHERE id=?',[p.real_id]);return row})();
   entries.district_id=town.district_id;entries.kind=name.endsWith('리')?'ri':'legal_dong';
  }else if(level==='area'){
   entries.town_id=p.level==='town'?p.real_id:p.town_id;
   entries.legal_unit_id=p.level==='ri'?p.legal_unit_id:null;
  }else {entries[data.fk]=p.real_id;if(level==='town')entries.kind=name.endsWith('읍')?'eup':name.endsWith('면')?'myeon':name.endsWith('동')?'dong':'other';}
  const cols=Object.keys(entries);
  const [r]=await c.query(`INSERT INTO ${data.table} (${cols.map(x=>'`'+x+'`').join(',')}) VALUES(${cols.map(()=>'?').join(',')})`,Object.values(entries));
  if(level==='ri')await c.query('INSERT INTO town_legal_links(district_id,town_id,legal_unit_id) VALUES(?,?,?)',[entries.district_id,p.real_id,r.insertId]);
  await c.commit();res.json({ok:true,message:'지역 등록 OK',id:virtual(level,r.insertId,level==='ri'?p.real_id:undefined)});
 }catch(e){await c.rollback();if(e.code==='ER_DUP_ENTRY')throw bad('같은 단계에 중복된 지역 또는 코드가 있습니다.',409);throw e}
 finally{c.release();}
}));
router.post('/admin/restaurants',needAdmin,wrap(async(req,res)=>{
 const tree=await loadTree(pool());const a=tree.find(x=>x.id===Number(req.body.location_id));
 if(!a||a.level!=='area')throw bad('읍·면·동 다음의 상권까지 선택한 후 음식점을 등록하세요.');
 const name=safeText(req.body.name,180);if(!name)throw bad('음식점명이 필요합니다.');
 const values={area_id:a.real_id,name,place_type:'restaurant',category:safeText(req.body.category,90),price_min:numberIn(req.body.price_min??0,0,100000000,'최저 가격'),price_max:req.body.price_max&&Number(req.body.price_max)>0?numberIn(req.body.price_max,0,100000000,'최고 가격'):null,address:safeText(req.body.address,255)||null,main_menu:safeText(req.body.main_menu,200)||null,latitude:req.body.latitude?numberIn(req.body.latitude,-90,90,'위도'):null,longitude:req.body.longitude?numberIn(req.body.longitude,-180,180,'경도'):null,google_place_id:safeText(req.body.google_place_id,200)||null,image_path:safeText(req.body.image_path,500)||null,rating:req.body.rating?numberIn(req.body.rating,0,5,'평점'):null,review_count:req.body.review_count?numberIn(req.body.review_count,0,10000000,'리뷰 수'):0,lunch_start:req.body.lunch_start||'11:00',lunch_end:req.body.lunch_end||'15:00'};
 if(values.price_max!=null&&values.price_min>values.price_max)throw bad('가격 범위가 잘못되었습니다.');
 const keys=Object.keys(values);
 try{const [r]=await pool().query(`INSERT INTO places(${keys.map(x=>'`'+x+'`').join(',')}) VALUES(${keys.map(()=>'?').join(',')})`,Object.values(values));res.json({ok:true,id:r.insertId,message:'음식점 등록 OK'})}
 catch(e){if(e.code==='ER_DUP_ENTRY')throw bad('이미 등록된 음식점 또는 Google Place ID입니다.',409);throw e}
}));
router.post('/admin/places',needAdmin,wrap(async(req,res)=>{
 const tree=await loadTree(pool()),area=tree.find(x=>x.id===Number(req.body.location_id));
 if(area?.level!=='area')throw bad('상권을 선택해야 장소를 등록할 수 있습니다.');
 const type=safeText(req.body.place_type,15);
 if(!['restaurant','attraction','cafe','lodging'].includes(type))throw bad('올바른 장소 종류를 선택하세요.');
 const name=safeText(req.body.name,180);if(!name)throw bad('장소명을 입력하세요.');
 const low=numberIn(req.body.price_min||0,0,100000000,'최저가격'),high=req.body.price_max&&Number(req.body.price_max)>0?numberIn(req.body.price_max,0,100000000,'최고가격'):null;
 if(high!=null&&low>high)throw bad('최고가격은 최저가격 이상이어야 합니다.');
 const columns=['area_id','name','place_type','category','address','price_min','price_max','latitude','longitude'];
 const args=[area.real_id,name,type,safeText(req.body.category,90)||null,safeText(req.body.address,255)||null,low,high,req.body.latitude?numberIn(req.body.latitude,-90,90,'위도'):null,req.body.longitude?numberIn(req.body.longitude,-180,180,'경도'):null];
 try{const [r]=await pool().query('INSERT INTO places ('+columns.join(',')+') VALUES ('+columns.map(()=>'?').join(',')+')',args);res.json({ok:true,id:r.insertId,message:'여행 장소 등록 OK'});}
 catch(e){if(e.code==='ER_DUP_ENTRY')throw bad('같은 상권에 이미 등록된 장소입니다.',409);throw e}
}));
router.post('/admin/sync-google-places',needAdmin,(req,res)=>res.status(501).json({message:'V8.4 통합판에서는 잘못된 지역에 실제 장소를 저장하지 않도록 자동 동기화를 잠시 중지했습니다. 상권 선택과 위·경도 검증을 포함한 동기화는 별도 검증 후 활성화합니다.'}));

// User membership
async function sessionUser(req,id){
 await new Promise((resolve,reject)=>req.session.regenerate(e=>e?reject(e):resolve()));
 req.session.userId=id;
 await new Promise((resolve,reject)=>req.session.save(e=>e?reject(e):resolve()));
}
router.post('/user/register',wrap(async(req,res)=>{
 const username=safeText(req.body.username,80),password=String(req.body.password??''),name=safeText(req.body.name,100);
 if(!/^[A-Za-z0-9가-힣_.-]{3,30}$/.test(username)||password.length<6||!name)throw bad('아이디 3~30자, 비밀번호 6자 이상, 이름이 필요합니다.');
 const password_hash=await bcrypt.hash(password,12);
 try{
  const [r]=await pool().query('INSERT INTO users(username,password_hash,display_name) VALUES(?,?,?)',[username,password_hash,name]);
  await sessionUser(req,r.insertId);res.json({ok:true,message:`회원등록 OK — ${name}님, 가입 및 자동 로그인 완료`,user:{id:r.insertId,name}});
 }catch(e){if(e.code==='ER_DUP_ENTRY')throw bad('이미 사용 중인 아이디입니다.',409);throw e}
}));
router.post('/user/login',wrap(async(req,res)=>{
 const username=safeText(req.body.username,80),pass=String(req.body.password??'');
 const user=await one('SELECT id,username,display_name,password_hash FROM users WHERE username=?',[username]);
 if(!user||!(await bcrypt.compare(pass,user.password_hash)))throw bad('아이디 또는 비밀번호가 일치하지 않습니다.',401);
 await sessionUser(req,user.id);res.json({ok:true,message:'로그인 OK',user:{id:user.id,name:user.display_name}});
}));
router.post('/user/logout',(req,res)=>req.session.destroy(()=>res.json({ok:true})));
router.get('/user/me',wrap(async(req,res)=>{
 if(!req.session.userId)return res.json({loggedIn:false});
 const u=await one(`SELECT u.id,u.username,u.display_name name,p.lunch_budget budget_max,p.group_size people,p.liked_food liked_categories,p.disliked_food disliked_categories,
 p.latitude,p.longitude,p.preferred_area_id work_area_id,d.id work_city_id
 FROM users u LEFT JOIN user_preferences p ON p.user_id=u.id LEFT JOIN admin_towns t ON t.id=p.preferred_town_id LEFT JOIN districts d ON d.id=t.district_id
 WHERE u.id=?`,[req.session.userId]);
 res.json(u?{loggedIn:true,user:u}:{loggedIn:false});
}));
router.put('/user/preferences',needUser,wrap(async(req,res)=>{
 const area=req.body.work_area_id?validId(req.body.work_area_id,'상권'):null;
 let town=null;
 if(area){const r=await one('SELECT town_id FROM commercial_areas WHERE id=?',[area]);if(!r)throw bad('선택한 상권이 존재하지 않습니다.');town=r.town_id;}
 else if(req.body.work_city_id){const r=await one('SELECT id FROM admin_towns WHERE district_id=? ORDER BY id LIMIT 1',[validId(req.body.work_city_id,'시군구')]);town=r?.id||null;}
 const budget=numberIn(req.body.budget_max??15000,1000,100000000,'예산');const people=numberIn(req.body.people??1,1,100,'인원');
 const values=[req.session.userId,town,area,budget,people,safeText(req.body.liked_categories,255),safeText(req.body.disliked_categories,255),req.body.latitude||null,req.body.longitude||null];
 await pool().query(`INSERT INTO user_preferences(user_id,preferred_town_id,preferred_area_id,lunch_budget,group_size,liked_food,disliked_food,latitude,longitude)
 VALUES(?,?,?,?,?,?,?,?,?) ON DUPLICATE KEY UPDATE preferred_town_id=VALUES(preferred_town_id),preferred_area_id=VALUES(preferred_area_id),lunch_budget=VALUES(lunch_budget),group_size=VALUES(group_size),liked_food=VALUES(liked_food),disliked_food=VALUES(disliked_food),latitude=VALUES(latitude),longitude=VALUES(longitude)`,values);
 res.json({ok:true,message:'내 조건 저장 OK'});
}));
router.get('/user/history',needUser,wrap(async(req,res)=>{
 const rows=await query(`SELECT h.id,h.action,h.visit_date,h.reject_reason,h.decision_score,h.created_at,p.name,p.category,p.image_path,p.price_min,p.price_max
 FROM lunch_history h JOIN places p ON p.id=h.place_id WHERE h.user_id=? ORDER BY h.created_at DESC LIMIT 100`,[req.session.userId]);
 res.json({rows:rows.map(r=>({...r,visit_date:r.visit_date||r.created_at}))});
}));
router.get('/user/learning',needUser,wrap(async(req,res)=>{
 const totals=await query('SELECT action,COUNT(*) n FROM lunch_history WHERE user_id=? GROUP BY action',[req.session.userId]);
 const t={};totals.forEach(x=>t[x.action]=Number(x.n));
 const categories=await query(`SELECT p.category,SUM(h.action='visited') visited,SUM(h.action='rejected') rejected
 FROM lunch_history h JOIN places p ON p.id=h.place_id WHERE h.user_id=? GROUP BY p.category ORDER BY visited DESC LIMIT 10`,[req.session.userId]);
 const reasons=await query("SELECT reject_reason,COUNT(*) count FROM lunch_history WHERE user_id=? AND reject_reason IS NOT NULL GROUP BY reject_reason ORDER BY count DESC LIMIT 8",[req.session.userId]);
 res.json({totals:t,categories,reasons});
}));

router.post('/recommendation/today',wrap(async(req,res)=>{
 let area=req.body.area_id?validId(req.body.area_id,'상권'):null;
 let city=req.body.city_id?validId(req.body.city_id,'시군구'):null;
 if(!area&&!city&&req.session.userId){const p=await one('SELECT preferred_area_id,preferred_town_id FROM user_preferences WHERE user_id=?',[req.session.userId]);area=p?.preferred_area_id||null;}
 if(!area&&!city)throw bad('먼저 국가부터 읍·면·동 및 상권을 선택하세요.');
 let sql=fullSql+" WHERE p.active=1 AND p.place_type='restaurant'";const args=[];
 if(area){sql+=' AND p.area_id=?';args.push(area);}else{sql+=' AND d.id=?';args.push(city)}
 const rows=await query(sql+' ORDER BY p.id LIMIT 200',args);
 if(!rows.length)throw bad('선택한 지역에 음식점이 없습니다. 다른 상권을 선택하거나 관리자에서 음식점을 등록하세요.',404);
 const pref=req.session.userId?await one('SELECT * FROM user_preferences WHERE user_id=?',[req.session.userId]):null;
 const budget=numberIn(req.body.budget_max??pref?.lunch_budget??15000,0,100000000,'점심 예산');
 const liked=safeText(pref?.liked_food||'',255).split(',').map(x=>x.trim()).filter(Boolean);
 const disliked=safeText(pref?.disliked_food||'',255).split(',').map(x=>x.trim()).filter(Boolean);
 const recents=req.session.userId?await query("SELECT place_id,action FROM lunch_history WHERE user_id=? AND created_at>=NOW()-INTERVAL 30 DAY",[req.session.userId]):[];
 const scored=rows.map(x=>{
  let score=Number(x.rating||0)*10+(x.is_demo?0:3),reasons=[];
  if(budget>=Number(x.price_min||0)){score+=20;reasons.push('예산 범위 충족')}else{score-=80;}
  if(liked.some(s=>(x.category||'').includes(s)))score+=12;
  if(disliked.some(s=>(x.category||'').includes(s)))score-=40;
  score-=recents.filter(y=>Number(y.place_id)===Number(x.id)&&y.action==='visited').length*12;
  score-=recents.filter(y=>Number(y.place_id)===Number(x.id)&&y.action==='rejected').length*20;
  return {...encode(x),score,reasons};
 }).sort((a,b)=>b.score-a.score||a.id-b.id);
 const w=scored[0];
 if(req.session.userId)await pool().query('INSERT INTO lunch_history(user_id,place_id,action,visit_date,decision_score) VALUES(?,?,\'recommended\',CURDATE(),?)',[req.session.userId,w.id,w.score]);
 const reasons=['선택한 지역의 실제 DB 등록 장소',...w.reasons];
 if(w.is_demo)reasons.push('샘플 장소: 실제 영업·가격 정보는 확인되지 않았습니다.');
 res.json({ok:true,winner:{...w,open_now:null,local_time:new Date().toLocaleTimeString('ko-KR',{hour:'2-digit',minute:'2-digit'})},reasons,candidates:scored.slice(0,5)});
}));
router.post('/recommendation/feedback',needUser,wrap(async(req,res)=>{
 if(!['visited','rejected'].includes(req.body.action))throw bad('방문 또는 거부 중 선택하세요.');
 const place=await one("SELECT id FROM places WHERE id=? AND place_type='restaurant'",[validId(req.body.restaurant_id,'음식점')]);if(!place)throw bad('음식점을 찾을 수 없습니다.',404);
 await pool().query('INSERT INTO lunch_history(user_id,place_id,action,visit_date,reject_reason) VALUES(?,?,?,CURDATE(),?)',[req.session.userId,place.id,req.body.action,safeText(req.body.reject_reason,200)||null]);res.json({ok:true});
}));

const cityCoords={서울특별시:[37.5665,126.978],부산광역시:[35.1796,129.0756],전북특별자치도:[35.82,127.15],도쿄도:[35.6762,139.6503],오사카부:[34.69,135.50]};
router.get('/context/today',wrap(async(req,res)=>{
 const key=process.env.OPENWEATHER_API_KEY;
 if(!key)return res.json({ok:false,weather:'날씨 API 키 없음',kind:'clear',message:'OPENWEATHER_API_KEY 미설정'});
 let lat=Number(req.query.lat),lon=Number(req.query.lon);let regionName='서울특별시';
 if(!Number.isFinite(lat)||!Number.isFinite(lon)||!lat||!lon){
  if(req.query.city_id){const p=await one('SELECT p.name FROM districts d JOIN provinces p ON p.id=d.province_id WHERE d.id=?',[Number(req.query.city_id)]);regionName=p?.name||regionName;}
  [lat,lon]=cityCoords[regionName]||cityCoords['서울특별시'];
 }
 try{
  const r=await fetch(`https://api.openweathermap.org/data/2.5/weather?lat=${lat}&lon=${lon}&units=metric&lang=kr&appid=${encodeURIComponent(key)}`,{signal:AbortSignal.timeout(6500)});
  if(!r.ok)throw Error(`OpenWeather HTTP ${r.status}`);
  const data=await r.json();const wx=data.weather?.[0];const rain=wx?.id>=200&&wx?.id<600,snow=wx?.id>=600&&wx?.id<700;
  const temp=Number(data.main?.temp);
  res.json({ok:true,source:'OpenWeather',temperature:temp,weather:wx?.description||'날씨 정보',kind:rain?'rain':snow?'snow':temp>28?'hot':temp<8?'cold':'clear',observedAt:new Date(data.dt*1000).toISOString()});
 }catch(e){res.json({ok:false,weather:'날씨 조회 실패',kind:'clear',message:e.message});}
}));
router.get('/map/route',wrap(async(req,res)=>{
 const from={latitude:Number(req.query.from_lat),longitude:Number(req.query.from_lng)},to={latitude:Number(req.query.to_lat),longitude:Number(req.query.to_lng)};
 const result=await between(from,to);res.json({ok:result.minutes!==null,...result});
}));
router.get('/travel/places',wrap(async(req,res)=>{
 const district=validId(req.query.city_id,'시군구');const params=[district];let sql=fullSql+' WHERE d.id=? AND p.active=1';
 if(req.query.type&&req.query.type!=='all'){sql+=' AND p.place_type=?';params.push(req.query.type==='hotel'?'lodging':req.query.type);}
 res.json({rows:(await query(sql+' ORDER BY p.id LIMIT 200',params)).map(encode)});
}));
router.post('/travel/auto-plan',wrap(async(req,res)=>{
 const city=validId(req.body.city_id,'시군구'),days=numberIn(req.body.days??1,1,7,'여행 일수');
 const places=(await query(fullSql+' WHERE d.id=? AND p.active=1',[city])).map(encode);
 const groups={attraction:places.filter(x=>x.place_type==='attraction'),cafe:places.filter(x=>x.place_type==='cafe'),restaurant:places.filter(x=>x.place_type==='restaurant'),lodging:places.filter(x=>x.place_type==='lodging')};
 const missing=Object.entries(groups).filter(([k,v])=>v.length===0).map(([k])=>k);
 if(missing.length)throw bad('여행코스를 만들기 위한 장소 데이터 부족: '+missing.join(', ')+'. 관리자에서 추가하세요.',409);
 const plan=[];let totalMin=0,totalDist=0;let unavailable=0,previous=null;
 for(let day=1;day<=days;day++){
  const choose=(type,exclude=[])=>groups[type].filter(p=>!exclude.includes(p.id))[0]||groups[type][0];
  const morning=choose('attraction'),lunch=choose('restaurant'),cafe=choose('cafe'),afternoon=choose('attraction',[morning.id]),dinner=choose('restaurant',[lunch.id]),hotel=choose('lodging');
  const record={day};
  for(const [key,p]of Object.entries({morning,lunch,cafe,afternoon,dinner,hotel})){
   let route={minutes:null,distanceKm:null};if(previous&&p){try{route=await between(previous,p)}catch(e){/* API error reported as unverified */}}
   if(previous&&route.minutes==null)unavailable++;
   if(route.minutes!=null){totalMin+=route.minutes;totalDist+=route.distanceKm;}
   record[key]={...p,travel_minutes:route.minutes,travel_distance_km:route.distanceKm};previous=p;
  }
  plan.push(record);
 }
 res.json({ok:true,plan,days,total_travel_minutes:totalMin,total_distance_km:Number(totalDist.toFixed(2)),note:unavailable?'좌표 또는 경로 API가 없어 일부 이동시간은 미확인입니다. 테스트 장소는 실제 영업시간을 보장하지 않습니다.':'OSRM 자동차 경로 기준 이동시간입니다. 영업시간·예약 가능 여부는 별도 확인이 필요합니다.'});
}));
router.get('/system/check',wrap(async(req,res)=>{
 const tables={};for(const t of ['countries','provinces','districts','admin_towns','town_legal_links','commercial_areas','places','users','user_preferences','lunch_history','migration_mappings'])tables[t]=Number((await one(`SELECT COUNT(*) n FROM ${t}`)).n);
 const orphanTown=Number((await one('SELECT COUNT(*) n FROM admin_towns t LEFT JOIN districts d ON d.id=t.district_id WHERE d.id IS NULL')).n);
 const orphanArea=Number((await one('SELECT COUNT(*) n FROM commercial_areas a LEFT JOIN admin_towns t ON t.id=a.town_id WHERE t.id IS NULL')).n);
 res.json({ok:true,database:true,version:'V8.4.1',dbName:db.database,tables,foreignKeys:{orphanTown,orphanArea},external:{openweatherConfigured:!!process.env.OPENWEATHER_API_KEY,googleConfigured:!!process.env.GOOGLE_MAPS_API_KEY}});
}));
router.get('/health',wrap(async(req,res)=>{await pool().query('SELECT 1');res.json({ok:true,version:'V8.4.1',database:db.database})}));
module.exports=router;
