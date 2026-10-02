/* Chromium checks against the isolated authenticated Django loopback bridge. */
const fs=require('node:fs'),path=require('node:path'),assert=require('node:assert/strict');
const cache=path.join(require('node:os').homedir(),'.npm/_npx');let modulePath;
for(const dir of fs.readdirSync(cache)){const p=path.join(cache,dir,'node_modules/playwright');if(fs.existsSync(p+'/package.json')&&JSON.parse(fs.readFileSync(p+'/package.json')).version==='1.55.0'){modulePath=p;break;}}
if(!modulePath)throw Error('Previously verified cached Playwright 1.55.0 unavailable');
const {chromium}=require(modulePath);const output=process.argv[2];if(!output||!output.startsWith('/tmp/task33-08-'))throw Error('Private QA output required');fs.mkdirSync(output,{recursive:true});
(async()=>{const browser=await chromium.launch({headless:true,args:['--no-sandbox']});const context=await browser.newContext();await context.route('**/*',route=>{const u=new URL(route.request().url());return u.hostname==='127.0.0.1'&&u.port==='8768'?route.continue():route.abort();});const page=await context.newPage();const result={browser:browser.version(),matrix:[],flows:[],external_requests_blocked:true,screenshots:[]};
try{
 for(const area of ['owner','admin'])for(const lang of ['az','ru','en'])for(const width of [320,360,390,768,1024,1280,1440]){
  await page.setViewportSize({width,height:900});const response=await page.goto(`http://127.0.0.1:8768/${area}?lang=${lang}`,{waitUntil:'networkidle'});assert.equal(response.status(),200);
  const token=page.locator('input[name="publication_token"], input[name="base_token"]');assert.equal(await token.count(),1);assert(await token.inputValue());assert.equal(await token.getAttribute('type'),'hidden');
  if(area==='admin'){const publish=page.locator('[data-pf-publish]').first();if(await publish.count())assert(await publish.isEnabled(),'Website-only ready card must permit publication');}
  const shot=`${area}-${lang}-${width}.png`;await page.screenshot({path:path.join(output,shot),fullPage:true});result.screenshots.push(shot);result.matrix.push({area,lang,width,status:'PASS'});
 }
 for(const area of ['owner','admin'])for(const lang of ['az','ru','en']){
  await page.goto(`http://127.0.0.1:8768/${area}?lang=${lang}`,{waitUntil:'networkidle'});
  if(area==='admin' && await page.locator('input[name="base_token"]').count()) assert(await page.locator('button[name="action"][value="admin_save"]').isEnabled(), 'Fresh candidate must allow admin save');
  await page.locator('[name="description_az"]').fill(`Browser candidate ${area} ${lang}`);
  const status=await page.evaluate(async({area,lang})=>{const form=document.querySelector('input[name="publication_token"], input[name="base_token"]').form;const body=new URLSearchParams();for(const[k,v]of new FormData(form))if(typeof v==='string')body.append(k,v);body.set('form_action','save_draft');body.set('_save_draft','1');if(area==='admin'&&form.querySelector('[name="base_token"]'))body.set('action','admin_save');body.delete('_publish_place');const r=await fetch(`/${area}?lang=${lang}`,{method:'POST',body});const status=Number(r.headers.get('X-QA-Django-Status'));const text=await r.text();const doc=new DOMParser().parseFromString(text,'text/html');return {status,errors:[...doc.querySelectorAll('.errorlist,.pw-form-errors,.pw-field__errors')].map(n=>n.textContent.trim()).filter(Boolean)};},{area,lang});assert.equal(status.status,302,`${area}/${lang} actual Django save: ${status.errors.join("; ")}`);
  const invariants=await (await context.request.get('http://127.0.0.1:8768/invariants')).json();assert(invariants.approved_description_preserved&&invariants.published_preserved&&invariants.candidate_present&&invariants.candidate_description_changed);result.flows.push({area,lang,status:'PASS',approved_preserved:true});
 }
 fs.writeFileSync(path.join(output,'results.json'),JSON.stringify(result,null,2));console.log(JSON.stringify({matrix:result.matrix.length,flows:result.flows.length,screenshots:result.screenshots.length,status:'PASS'}));
}catch(error){fs.writeFileSync(path.join(output,'results.json'),JSON.stringify({...result,status:'FAIL',error:error.message},null,2));throw error;}finally{await context.close();await browser.close();}})().catch(e=>{console.error(e.message);process.exitCode=1;});
