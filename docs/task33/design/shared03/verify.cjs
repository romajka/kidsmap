/* Reproducible real-browser prototype acceptance. No Django, DB or external API. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { pathToFileURL } = require('node:url');
let pwPath = process.env.STAGE03_PLAYWRIGHT_MODULE;
if (!pwPath) {
  try { pwPath = require.resolve('playwright'); }
  catch {
    const cache = path.join(require('node:os').homedir(), '.npm/_npx');
    if (fs.existsSync(cache)) for (const dir of fs.readdirSync(cache)) {
      const candidate = path.join(cache, dir, 'node_modules/playwright');
      if (fs.existsSync(candidate + '/package.json') && JSON.parse(fs.readFileSync(candidate + '/package.json')).version === '1.55.0') { pwPath = candidate; break; }
    }
  }
}
if (!pwPath) throw new Error('Playwright is unavailable. Set STAGE03_PLAYWRIGHT_MODULE to an existing Playwright library.');
const { chromium } = require(pwPath);
const base=process.env.STAGE03_BASE_URL||'http://127.0.0.1:8763/docs/task33/design/';
const result={revision:'admin-public-03-r1',generated_at:new Date().toISOString(),transport:'loopback static HTTP only',matrix:[],flows:[],screenshots:[],errors:[],external:[],status:'RUNNING'};
const widths=[320,360,390,768,1024,1280,1440],languages=['az','ru','en'];
const screens={admin:['index','organization','place','groups','review','transfer'],public:['index','catalog','organization','place','activity','events','event']};
const cases=[];
for(const [area,ss] of Object.entries(screens))for(const s of ss)cases.push([area,s,{}],[area,s,{long:'1'}]);
for(const state of ['conflict','new','program'])cases.push(['admin','review',{state}]);
for(const s of ['organization','place','activity'])cases.push(['public',s,{missing:'1'}]);
cases.push(['public','place',{missing:'1',sample:'park'}],['public','events',{view:'calendar'}],['public','events',{view:'calendar',month:'2026-09',occurrence:'all'}]);
for(const event of ['online','canceled','past'])cases.push(['public','event',{event}]);
let browser,page;
const url=(area,screen,q={})=>`${base}${area}/${screen}.html?${new URLSearchParams({lang:'ru',...q})}`;
async function load(area,screen,q={},w=390){await page.setViewportSize({width:w,height:900});await page.goto(url(area,screen,q));await page.evaluate(()=>document.fonts.ready);await page.locator('h1').waitFor();}
async function layout(){const m=await page.evaluate(()=>{const vw=document.documentElement.clientWidth;return {vw,sw:document.documentElement.scrollWidth,overflow:[...document.querySelectorAll('main *')].filter(el=>{let r=el.getBoundingClientRect();return r.width&&r.height&&(r.right>vw+1||r.left< -1)}).slice(0,5).map(el=>el.tagName+'.'+el.className),unnamed:[...document.querySelectorAll('input,select,textarea')].filter(el=>!el.labels.length&&!el.getAttribute('aria-label')).map(el=>el.id),duplicate:[...document.querySelectorAll('[id]')].map(el=>el.id).filter((id,i,all)=>all.indexOf(id)!==i),lang:document.documentElement.lang};});assert(m.sw<=m.vw+1,JSON.stringify(m));assert.deepEqual(m.overflow,[],page.url());assert.deepEqual(m.unnamed,[],page.url());assert.deepEqual(m.duplicate,[],page.url());return m;}
async function flow(name,fn){await fn();result.flows.push({name,status:'PASS'});}
async function shot(area,name){const file=`${area}/screenshots/${name}.png`;await page.screenshot({path:path.join(__dirname,'..',file),fullPage:true});result.screenshots.push({file,width:page.viewportSize().width,url:page.url().replace(base,'')});}
(async()=>{for(const area of Object.keys(screens))fs.mkdirSync(path.join(__dirname,'..',area,'screenshots'),{recursive:true});browser=await chromium.launch({headless:true});result.browser=browser.version();const context=await browser.newContext({reducedMotion:'reduce'});page=await context.newPage();page.on('console',m=>{if(m.type()==='error')result.errors.push(m.text())});page.on('pageerror',e=>result.errors.push(e.message));page.on('requestfailed',r=>result.errors.push(r.url()+':'+r.failure().errorText));page.on('response',r=>{if(r.status()>=400)result.errors.push(r.status()+' '+r.url());});await context.route('**/*',route=>{if(!route.request().url().startsWith('http://127.0.0.1:8763/')){result.external.push(route.request().url());return route.abort();}return route.continue();});
for(const [area,s,q] of cases)for(const lang of languages)for(const w of widths){await load(area,s,{...q,lang},w);const metrics=await layout();assert.equal(metrics.lang,lang);await page.keyboard.press('Tab');const focus=await page.evaluate(()=>({tag:document.activeElement.tagName,outline:getComputedStyle(document.activeElement).outlineStyle}));assert.notEqual(focus.tag,'BODY');assert.notEqual(focus.outline,'none');result.matrix.push({area,screen:s,query:{...q,lang},width:w,status:'PASS'});}
console.log('MATRIX PASS',result.matrix.length);
for(const lang of languages){
 await flow(`${lang}: review reject requires reason and retains input`,async()=>{await load('admin','review',{lang});await page.locator('#reject').click();assert.equal(await page.locator('#review-note').getAttribute('aria-invalid'),'true');await page.locator('#review-note').fill('Synthetic reason');await page.locator('#reject').click();assert(await page.locator('dialog').isVisible());await page.keyboard.press('Escape');assert.equal(await page.locator('#review-note').inputValue(),'Synthetic reason');assert.equal(await page.evaluate(()=>document.activeElement.id),'reject');});
 await flow(`${lang}: approve dialog keyboard trap and restore`,async()=>{await page.locator('#approve').click();for(let i=0;i<8;i++){await page.keyboard.press('Tab');assert(['dialog-close','dialog-confirm'].includes(await page.evaluate(()=>document.activeElement.id)));}for(let i=0;i<8;i++){await page.keyboard.press('Shift+Tab');assert(['dialog-close','dialog-confirm'].includes(await page.evaluate(()=>document.activeElement.id)));}await page.locator('#dialog-confirm').click();assert(await page.locator('#feedback').isVisible());assert.equal(await page.evaluate(()=>document.activeElement.id),'approve');});
 await flow(`${lang}: conflict blocks approve`,async()=>{await load('admin','review',{lang,state:'conflict'});assert.equal(await page.locator('#approve').count(),0);assert(await page.locator('button:disabled').isVisible());});
 await flow(`${lang}: program impact explicit`,async()=>{await load('admin','review',{lang,state:'program'});assert.equal(await page.locator('.rows li').count(),2);await page.locator('#approve').click();assert(await page.locator('#dialog-copy').textContent());await page.keyboard.press('Escape');});
 await flow(`${lang}: transfer requires consent`,async()=>{await load('admin','transfer',{lang});await page.locator('#transfer').click();assert.equal(await page.evaluate(()=>document.activeElement.id),'transfer-check');await page.locator('#transfer-check').check();await page.locator('#transfer').click();assert(await page.locator('dialog').isVisible());await page.keyboard.press('Escape');});
 await flow(`${lang}: catalog filter survives map and reset`,async()=>{await load('public','catalog',{lang});await page.locator('#activity-filter').selectOption('robotics');assert.equal(await page.locator('[data-place]:visible').count(),1);await page.locator('#catalog-map').click();assert.equal(await page.locator('#activity-filter').inputValue(),'robotics');await page.locator('#venue').click();assert(await page.locator('#venue-results').isVisible());await page.locator('#catalog-list').click();await page.locator('#reset').click();assert.equal(await page.locator('[data-place]:visible').count(),3);});
 await flow(`${lang}: org search has independent result`,async()=>{await page.locator('#search').fill({az:'Kəşf şəbəkəsi',ru:'Сеть «Открытие»',en:'Discovery network'}[lang]);assert(await page.locator('#org-discovery').isVisible());});
 await flow(`${lang}: calendar format/view/month URL preservation`,async()=>{await load('public','events',{lang,view:'calendar'});await page.locator('#event-format').selectOption('online');assert.equal(await page.locator('.event-row').count(),1);await page.locator('#event-list').click();assert.equal(await page.locator('#event-format').inputValue(),'online');await page.locator('#event-calendar').click();await page.locator('[data-date="2026-10-04"]').click();assert.equal(await page.locator('.event-row').count(),0);assert(await page.locator('.empty-result').isVisible());await page.locator('#prev-month').click();let u=new URL(page.url());assert.equal(u.searchParams.get('month'),'2026-09');assert.equal(u.searchParams.get('format'),'online');await page.reload();assert.equal(await page.locator('#event-format').inputValue(),'online');assert.equal(await page.locator('#event-calendar').getAttribute('aria-pressed'),'true');});
 await flow(`${lang}: canceled and past remain reachable`,async()=>{await load('public','events',{lang,view:'calendar',occurrence:'all'});await page.locator('[data-date="2026-10-04"]').click();assert.equal(await page.locator('.event-row').count(),1);await page.locator('#prev-month').click();await page.locator('[data-date="2026-09-20"]').click();assert.equal(await page.locator('.event-row').count(),1);});
}
for(const [area,ss] of Object.entries(screens))for(const s of ss)for(const w of [390,1280]){await load(area,s,{},w);await shot(area,`${s}-ru-${w}`);}
for(const state of ['conflict','new','program'])for(const w of [390,1280]){await load('admin','review',{state},w);await shot('admin',`review-${state}-ru-${w}`);}
for(const event of ['online','canceled','past'])for(const w of [390,1280]){await load('public','event',{event},w);await shot('public',`event-${event}-ru-${w}`);}
for(const w of [390,1280]){await load('public','events',{view:'calendar',occurrence:'all'},w);await shot('public',`events-calendar-ru-${w}`);await load('public','place',{sample:'park',missing:'1'},w);await shot('public',`place-missing-ru-${w}`);for(const lang of ['az','en']){await load('public','place',{lang,long:'1',missing:'1'},w);await shot('public',`place-long-missing-${lang}-${w}`);}}
assert.deepEqual(result.errors,[]);assert.deepEqual(result.external,[]);result.status='PASS';console.log(`PASS: ${result.matrix.length} rendered cases, ${result.flows.length} flows, ${result.screenshots.length} screenshots; errors 0/external 0`);
})().catch(e=>{result.status='FAIL';result.failure=e.stack;console.error(e);process.exitCode=1;}).finally(async()=>{if(browser)await browser.close();fs.writeFileSync(path.join(__dirname,'verification.json'),JSON.stringify(result,null,2)+'\n');});
