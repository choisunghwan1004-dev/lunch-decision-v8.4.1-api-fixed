require('dotenv').config();
const fs=require('node:fs'),path=require('node:path'),db=require('../db');
(async()=>{
 if(db.database!=='lunch_decision_v83'||db.database===db.oldDatabase)throw Error('안전 차단: V83_DB_NAME=lunch_decision_v83만 허용');
 const src=fs.readFileSync(path.join(__dirname,'../sql/03_news_v851.sql'),'utf8');
 const conn=await db.mysql.createConnection({...db.config,database:db.database,multipleStatements:true,connectTimeout:9000});
 try{
  await conn.query(src);
  const [r]=await conn.query("SELECT table_name FROM information_schema.tables WHERE table_schema=DATABASE() AND table_name LIKE 'news_%'");
  console.log('뉴스 DB 스키마 생성 OK / 테이블 수:',r.length);
 }finally{await conn.end()}
})().catch(e=>{console.error('뉴스 DB 스키마 오류:',e.code||'',e.message);process.exitCode=1});
