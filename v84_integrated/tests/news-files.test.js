const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs'),path=require('node:path');
const root=path.resolve(__dirname,'..');const read=p=>fs.readFileSync(path.join(root,p),'utf8');
test('existing API is preserved',()=>assert.match(read('server.js'),/app.use\('\/api',api\)/));
test('news API is authenticated through Node',()=>assert.match(read('routes/news-proxy.js'),/req.session\?\.adminId/));
test('administrator has separate news tab',()=>assert.match(read('public/admin.html'),/show\('news'\)/));
test('legacy admin panels are preserved',()=>{let s=read('public/admin.html');['location','restaurant','sync','places'].forEach(id=>assert.ok(s.includes('id="'+id+'"')))});
test('.env ignored',()=>assert.match(read('.gitignore'),/^\.env$/m));
