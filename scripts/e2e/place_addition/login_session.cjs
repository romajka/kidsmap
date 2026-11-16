const assert=require('node:assert/strict');

// Only cookies obtained through the real login form are reused. Nothing is
// written to disk; each scenario still gets a fresh DOM and local storage.
const browsers=new WeakMap();
async function withLoginSession(context,{user,origin,language,admin},signIn){
 assert(['127.0.0.1','localhost'].includes(new URL(origin).hostname),'Only localhost QA is allowed');
 const browser=context.browser();
 let users=browsers.get(browser);if(!users){users=new WeakMap();browsers.set(browser,users);}
 let sessions=users.get(user);if(!sessions){sessions=new Map();users.set(user,sessions);}
 const key=JSON.stringify([origin,language,admin]);
 const saved=sessions.get(key);
 if(saved){
  await context.addCookies(saved.cookies);
  const page=await context.newPage();await page.goto(saved.url);
  const target=new URL(page.url());
  assert(target.origin===origin&&!target.pathname.includes('/login/'),'Restored QA session was rejected');
  return page;
 }
 const page=await signIn();
 const target=new URL(page.url());
 assert(target.origin===origin&&!target.pathname.includes('/login/'),'Initial QA login did not create a session');
 const cookies=await context.cookies(origin);
 assert(cookies.length,'Authenticated QA context has no cookies');
 sessions.set(key,{cookies,url:page.url()});
 return page;
}
module.exports={withLoginSession};
