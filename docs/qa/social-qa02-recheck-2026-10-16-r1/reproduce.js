async original=>{
const B='http://127.0.0.1:33741',H='/home/ramin/kidsmap/docs/qa/social-qa02-recheck-2026-10-16-r1',F=await(await original.request.get(B+'/qa/fixtures/')).json(),f=F.cases[0],rows=[],diagnostics=[],contexts=[];let kind='',lang='',width=390,scenario='';
const add=(id,ok,extra={})=>rows.push({id,kind,lang,width,scenario,status:ok?'PASS':'FAIL',...extra});
const prefix=l=>l==='az'?'/':'/'+l+'/';
function text(role,k){return 'Fictional SOCIAL01 0 '+role+' '+k+' '+(role==='author'?'candidate-two':'first')+' <script>window.SOCIAL01_XSS=1</script> & <b>literal</b>'+' LongWord'.repeat(8);}
async function login(role,l,w){const c=await original.context().browser().newContext({viewport:{width:w,height:950}});contexts.push(c);await c.route('**/*',r=>r.request().url().startsWith(B+'/')?r.continue():r.abort());const p=await c.newPage();p.on('pageerror',e=>diagnostics.push({type:'pageerror',error:String(e)}));p.on('response',r=>{if(r.url().startsWith(B+'/')&&r.status()>=400)diagnostics.push({type:'local-http',status:r.status()});});p.on('console',m=>{if(m.type()==='error'&&m.location().url.startsWith(B+'/'))diagnostics.push({type:'local-console',text:m.text()});});await p.goto(B+prefix(l)+'auth/login/');await p.locator('[name=username]').fill(f.actors[role].username);await p.locator('[name=password]').fill(F.password);await Promise.all([p.waitForURL(u=>!u.pathname.includes('/auth/login/'),{waitUntil:'domcontentloaded'}),p.locator('form.register-form--login button[type=submit]').click()]);return p;}
try{
for(const [l,w,kinds]of[['ru',390,['place','specialist','activity','event']],['az',390,['specialist']],['az',1440,['specialist']],['en',390,['specialist']],['en',1440,['specialist']]]){
 lang=l;width=w;for(const [state,role]of[['rejected-edit','author'],['rejected-first','rejected']]){scenario=state;const p=await login(role,l,w);
 for(kind of kinds){await p.goto(B+prefix(l)+'reviews/'+kind+'/target/'+f.targets[kind]+'/');await p.reload();const body=await p.locator('main.typed-reviews').innerText(),editor=await p.locator('#review-text').inputValue();
 add('saved rejection reason is visible to its author',body.includes('Fictional rejection for rating readback'));
 add('rejected revision text is available to its author',body.includes(text(role,kind))||editor===text(role,kind));
 add('SOCIAL01 saved rating still restored',await p.locator('#review-rating').inputValue()===(role==='author'?'4':'3'));
 add('literal content does not execute',await p.evaluate(()=>window.SOCIAL01_XSS===undefined));
 await p.locator('[data-review-edit]').scrollIntoViewIfNeeded();await p.screenshot({path:H+'/screenshots/'+state+'-'+lang+'-'+width+'-'+kind+'.png'});
 }
}}
return{complete:true,rows,diagnostics,mode:'PLAN ONLY SOCIAL-QA-02; fresh native reload of current synthetic rejection states; actual submit/reject transitions attributed to same-source SOCIAL01 fix flow',browser_version:original.context().browser().version()};
}catch(e){return{complete:false,error:String(e),rows,diagnostics};}finally{for(const c of contexts)await c.close();}
}
