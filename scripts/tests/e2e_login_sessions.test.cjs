const {test}=require('node:test');
const assert=require('node:assert/strict');
const {withLoginSession}=require('../e2e/place_addition/login_session.cjs');
const origin='http://127.0.0.1:8898';
const cookie={name:'sessionid',value:'synthetic-session',domain:'127.0.0.1',path:'/',httpOnly:true,secure:false,sameSite:'Lax',expires:-1};
function context(browser,redirect){
 const c={restored:null,browser:()=>browser,cookies:async()=>[cookie],addCookies:async value=>{c.restored=value;},
  newPage:async()=>({current:origin+'/admin/',url(){return this.current;},async goto(url){this.current=redirect||url;}})};
 return c;
}
function options(user,extra={}){return {user,origin,language:'ru',admin:true,...extra};}
test('eighty fresh contexts reuse one real login without losing cookie security flags',async()=>{
 const browser={},user={username:'fixture-admin'};let logins=0;
 for(let n=0;n<80;n++){
  const c=context(browser);const p=await withLoginSession(c,options(user),async()=>{logins++;return c.newPage();});
  assert.equal(p.url(),origin+'/admin/');if(n)assert.deepEqual(c.restored,[cookie]);
 }
 assert.equal(logins,1);
});
test('different users, languages, origins and browsers cannot share sessions',async()=>{
 const browser={},user={username:'admin'};let logins=0;
 for(const [b,o] of [[browser,options(user)],[browser,options({username:'owner'})],
  [browser,options(user,{language:'az'})],[{},options(user)],
  [browser,options(user,{origin:'http://localhost:8898'})]]){
  const c=context(b);await withLoginSession(c,o,async()=>{logins++;const p=await c.newPage();await p.goto(o.origin+'/admin/');return p;});
  assert.equal(c.restored,null);
 }
 assert.equal(logins,5);
});
test('failed initial login is not cached',async()=>{
 const browser={},user={};let logins=0;
 await assert.rejects(withLoginSession(context(browser),options(user),async()=>{logins++;throw Error('synthetic rejection');}));
 const c=context(browser);await withLoginSession(c,options(user),async()=>{logins++;return c.newPage();});
 assert.equal(logins,2);
});
test('an expired restored session fails without repeated password submissions',async()=>{
 const browser={},user={};const c=context(browser);
 await withLoginSession(c,options(user),()=>c.newPage());
 let calls=0;await assert.rejects(withLoginSession(context(browser,origin+'/admin/login/'),options(user),async()=>{calls++;}),/session/i);
 assert.equal(calls,0);
});
test('non-local destinations are refused before authentication',async()=>{
 let calls=0;await assert.rejects(withLoginSession(context({}),options({},{origin:'https://kidsmap.az'}),async()=>{calls++;}),/localhost/i);
 assert.equal(calls,0);
});
