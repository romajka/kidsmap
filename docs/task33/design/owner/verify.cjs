/* Reproducible real-browser prototype acceptance. No Django, DB or external API. */
const fs = require('node:fs');
const path = require('node:path');
const assert = require('node:assert/strict');
const { pathToFileURL } = require('node:url');
let pwPath = process.env.OWNER_PLAYWRIGHT_MODULE;
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
if (!pwPath) throw new Error('Playwright is unavailable. Set OWNER_PLAYWRIGHT_MODULE to an existing Playwright library.');
const { chromium } = require(pwPath);
const base = process.env.OWNER_BASE_URL || pathToFileURL(__dirname + '/').href;
const out = __dirname;
const screens = ['index', 'place', 'organization', 'cabinet', 'program', 'groups', 'team'];
const widths = [320, 360, 390, 768, 1024, 1280, 1440];
const languages = ['az', 'ru', 'en'];
const states = ['empty', 'draft', 'saving', 'save-failed', 'browser-only', 'pending', 'rejected', 'conflict', 'published-pending'];
const url = (screen, query = {}) => `${base}${screen}.html?${new URLSearchParams({ lang: 'ru', ...query })}`;
const result = {revision:'owner-02-r1',generated_at:new Date().toISOString(),mode:'synthetic static prototypes',transport:base.startsWith('file:')?'file':'loopback HTTP',browser:'',playwright:JSON.parse(fs.readFileSync(path.join(path.dirname(require.resolve(pwPath)), 'package.json'))).version,matrix:[],flows:[],screenshots:[],console_errors:[],page_errors:[],failed_resources:[],external_requests:[],status:'RUNNING'};
let browser;
let page;
async function load(screen, query = {}, width = 390) {
  await page.setViewportSize({width,height:900});
  await page.goto(url(screen,query));
  await page.evaluate(() => document.fonts.ready);
  await page.locator('h1').waitFor();
}
async function layout(label) {
  const metrics = await page.evaluate(() => {
    const width = document.documentElement.clientWidth;
    const offenders = [...document.querySelectorAll('main *')].filter(el => {
      const r = el.getBoundingClientRect();
      return r.width > 0 && r.height > 0 && (r.right > width + 1 || r.left < -1);
    }).slice(0,8).map(el=>`${el.tagName}.${el.className}`);
    const unnamed = [...document.querySelectorAll('input:not([hidden]),select,textarea')].filter(el=> !el.labels?.length && !el.getAttribute('aria-label')).map(el=>el.id);
    const duplicateIds = [...document.querySelectorAll('[id]')].map(el=>el.id).filter((id,i,ids)=>ids.indexOf(id)!==i);
    return {viewport:width,scroll:document.documentElement.scrollWidth,offenders,unnamed,duplicateIds,lang:document.documentElement.lang};
  });
  assert(metrics.scroll <= metrics.viewport+1, `${label}: horizontal overflow ${JSON.stringify(metrics)}`);
  assert.deepEqual(metrics.offenders,[],`${label}: visible element overflow`);
  assert.deepEqual(metrics.unnamed,[],`${label}: unlabeled form control`);
  assert.deepEqual(metrics.duplicateIds,[],`${label}: duplicate IDs`);
  return metrics;
}
async function flow(name, fn) {await fn();result.flows.push({name,status:'PASS'});}
async function screenshot(name) {const filename=`screenshots/${name}.png`;await page.screenshot({path:path.join(out,filename),fullPage:true});result.screenshots.push({file:filename,url:page.url().replace(base,''),width:page.viewportSize().width});}
(async()=>{
  fs.mkdirSync(path.join(out,'screenshots'),{recursive:true});
  browser=await chromium.launch({headless:true});
  result.browser=`Chromium ${browser.version()}`;
  const context=await browser.newContext({reducedMotion:'reduce'});
  page=await context.newPage();
  page.on('console',msg=>{if(msg.type()==='error')result.console_errors.push(msg.text());});
  page.on('pageerror',err=>result.page_errors.push(err.message));
  page.on('requestfailed',request=>result.failed_resources.push({url:request.url().replace(base,''),error:request.failure()?.errorText}));
  page.on('response',response=>{if(response.status()>=400)result.failed_resources.push({url:response.url().replace(base,''),status:response.status()});});
  page.on('request',request=>{if(/^https?:/.test(request.url()) && !/^http:\/\/(127\.0\.0\.1|localhost)(:|\/)/.test(request.url()))result.external_requests.push(request.url());});
  const variants=[...screens.map(screen=>({screen,query:{}})),{screen:'place',query:{sample:'park'}},{screen:'place',query:{sample:'network'}},{screen:'cabinet',query:{sample:'empty'}},{screen:'cabinet',query:{sample:'org-empty'}}];
  for (const variant of variants) for(const lang of languages) for(const width of widths) {
    await load(variant.screen,{...variant.query,lang,long:'1'},width);
    const metrics=await layout(`${variant.screen}/${JSON.stringify(variant.query)}/${lang}/${width}/long`);
    assert.equal(metrics.lang,lang);
    result.matrix.push({screen:variant.screen,...variant.query,lang,width,long:true,status:'PASS'});
  }
  for(const state of states) for(const lang of languages) for(const width of widths) {
    await load('place',{sample:'network',state,lang,long:'1'},width);
    await layout(`state ${state}/${lang}/${width}`);
    const text=await page.locator('#save-status').innerText();assert(text.trim().length>20);
    result.matrix.push({screen:'place',sample:'network',state,lang,width,long:true,status:'PASS'});
  }
  for (const lang of languages) {
    await flow(`continuous sections + keyboard navigation (${lang})`,async()=>{
      await load('place',{lang,state:'empty'});
      assert.equal(await page.locator('form section:visible').count(),4);
      await page.keyboard.press('Tab');assert.equal(await page.locator(':focus').getAttribute('class'),'skip');
      await page.locator('.side-nav a[href="#section-3"]').focus();await page.keyboard.press('Enter');
      assert.equal(await page.locator(':focus').getAttribute('id'),'section-3-title');
      await page.locator('#name-az').focus();
      assert.equal(await page.locator('#name-az').evaluate(el=>getComputedStyle(el).outlineStyle),'solid');
      const orgDetails=page.locator('details').filter({has:page.locator('#organization')});
      await orgDetails.locator('summary').focus();await page.keyboard.press('Enter');assert(await orgDetails.getAttribute('open')!==null);
    });
    await flow(`required errors, empty draft, standalone park (${lang})`,async()=>{
      await load('place',{lang,state:'empty',sample:'park'});
      await page.locator('button[type="submit"]').click();
      assert.equal(await page.locator('#name-az').getAttribute('aria-invalid'),'true');
      assert.equal(await page.locator('#address').getAttribute('aria-invalid'),'true');
      assert.equal(await page.locator(':focus').getAttribute('id'),'name-az');
      assert((await page.locator('#name-az').getAttribute('aria-describedby')).includes('name-az-error'));
      await page.locator('[data-action="save"]').click();await page.waitForTimeout(700);
      assert.equal(await page.locator('#name-az').inputValue(),'');
      await page.locator('#name-az').fill('Yaşıl Ada · sintetik park');await page.locator('#address').fill('Nümunə bağ yolu 8');
      await page.locator('button[type="submit"]').click();
      assert.equal(await page.locator('#organization').inputValue(),'');
      assert.equal(await page.locator('#activity-name').inputValue(),'');
      assert.equal(await page.locator('#contact-error').isVisible(),false);
      assert.equal(await page.locator('#save-status .status-box').getAttribute('aria-busy'),'false');
      const expected=await page.evaluate(lang=>window.OWNER_COPY.pendingTitle[{ru:0,az:1,en:2}[lang]],lang);
      assert((await page.locator('#save-status').innerText()).includes(expected));
    });
    await flow(`save failure and retry preserve input (${lang})`,async()=>{
      await load('place',{lang,state:'save-failed'});
      const before=await page.locator('#name-az').inputValue();
      await page.locator('[data-action="retry"]').click();
      assert.equal(await page.locator('#save-status .status-box').getAttribute('aria-busy'),'true');
      await page.waitForTimeout(700);assert.equal(await page.locator('#name-az').inputValue(),before);
    });
    await flow(`conflict comparison, focus trap and restore (${lang})`,async()=>{
      await load('place',{lang,state:'conflict',sample:'network'});
      await page.locator('#name-az').fill('Mənim saxlanmamış variantım');
      await page.locator('[data-action="compare"]').click();
      assert(await page.locator('#compare-dialog').evaluate(el=>el.open));
      assert.equal(await page.locator('#compare-local').innerText(),'Mənim saxlanmamış variantım');
      for(let i=0;i<9;i++){await page.keyboard.press('Tab');assert(await page.locator(':focus').evaluate(el=>Boolean(el.closest('dialog'))));}
      await page.keyboard.press('Escape');assert.equal(await page.locator(':focus').getAttribute('data-action'),'compare');
      assert.equal(await page.locator('#name-az').inputValue(),'Mənim saxlanmamış variantım');
      await page.locator('[data-action="compare"]').click();await page.locator('[data-action="resolve"]').click();
      assert.equal(await page.locator('#name-az').inputValue(),'Mənim saxlanmamış variantım');
      await page.locator('[data-action="save"]').click();await page.waitForTimeout(700);
    });
    await flow(`published listing remains visible through autosave and submit (${lang})`,async()=>{
      await load('place',{lang,sample:'network',state:'published-pending'});
      await page.locator('#description-az').fill('Yeni təsvir · sintetik məlumat');await page.waitForTimeout(1000);
      const expected=await page.evaluate(lang=>window.OWNER_COPY.publishedBody[{ru:0,az:1,en:2}[lang]],lang);
      assert((await page.locator('#save-status').innerText()).includes(expected),'Published public version must remain explained during draft saving');
      await page.locator('button[type="submit"]').click();
      const title=await page.evaluate(lang=>window.OWNER_COPY.publishedTitle[{ru:0,az:1,en:2}[lang]],lang);
      assert((await page.locator('#save-status').innerText()).includes(title),'Submit must retain published+pending state');
    });
    await flow(`contact provenance + local override + detach (${lang})`,async()=>{
      await load('place',{lang,sample:'network'});
      assert((await page.locator('[data-contact-source]').innerText()).includes('network.example.test'));
      await page.locator('#website').fill('https://branch.example.test');
      assert(!(await page.locator('[data-contact-source]').innerText()).includes('network.example.test'));
      await page.locator('#website').fill('');await page.locator('#organization').selectOption('');
      assert(!(await page.locator('[data-contact-source]').innerText()).includes('network.example.test'));
      assert.equal(await page.locator('#website').inputValue(),'');
    });
    await flow(`organization has no required address or branch (${lang})`,async()=>{
      await load('organization',{lang});assert.equal(await page.locator('#address').count(),0);
      await page.locator('button[type="submit"]').click();await page.waitForURL(/sample=org-empty/);
      assert.equal(await page.locator('.empty').count(),1);
    });
    await flow(`local group amount/schedule vs changed conditions (${lang})`,async()=>{
      await load('groups',{lang});await page.locator('#class-schedule').fill('Şənbə 10:00–11:00');await page.locator('#price').fill('90');
      await page.locator('button[type="submit"]').click();
      const amountTitle=await page.evaluate(lang=>window.OWNER_COPY.groupSaved[{ru:0,az:1,en:2}[lang]],lang);
      assert((await page.locator('#save-status').innerText()).includes(amountTitle));
      await page.locator('#conditions').fill('Yeni əsas şərtlər');await page.locator('button[type="submit"]').click();
      assert(await page.locator('#save-status .warning').isVisible());
      await page.locator('#no-upper').check();assert(await page.locator('#age-to').isDisabled());
      await load('groups',{lang});await page.locator('#name-az').fill('Yeni qrup adı');await page.locator('button[type="submit"]').click();assert(await page.locator('#save-status .warning').isVisible());
    });
    await flow(`employee selected branches never imply future network (${lang})`,async()=>{
      await load('team',{lang});await page.locator('#branch-narimanov').check();
      assert(await page.locator('#scope-selected').isChecked());assert(!(await page.locator('#scope-all').isChecked()));
      await page.locator('#scope-all').check();assert.equal(await page.locator('#selected-branches').isVisible(),false);
      await page.locator('#scope-selected').check();await page.locator('#branch-yasamal').uncheck();await page.locator('#branch-narimanov').uncheck();
      await page.locator('button[type="submit"]').click();assert(await page.locator('#scope-error').isVisible());
      await page.locator('#preset').selectOption('manager');assert(await page.locator('#permission-4').isChecked());
      await page.locator('#branch-yasamal').check();await page.locator('button[type="submit"]').click();assert(await page.locator('#invitation-status .status-box').isVisible());
    });
  }
  await flow('photo is marked unsaved before simulated success',async()=>{
    await load('place');await page.locator('#photo-file').setInputFiles({name:'synthetic.svg',mimeType:'image/svg+xml',buffer:Buffer.from('<svg xmlns="http://www.w3.org/2000/svg" width="100" height="100"><rect width="100" height="100" fill="#cde7c5"/></svg>')});
    assert.equal(await page.locator('#photo-preview').isVisible(),false);await page.waitForTimeout(650);assert(await page.locator('#photo-preview').isVisible());
  });
  const capture=[...screens.map(screen=>({screen,query:{},name:screen})),{screen:'place',query:{sample:'park'},name:'place-park'},{screen:'cabinet',query:{sample:'empty'},name:'cabinet-empty'},{screen:'cabinet',query:{sample:'org-empty'},name:'cabinet-org-empty'},...states.map(state=>({screen:'place',query:{sample:'network',state},name:`place-${state}`}))];
  for(const item of capture)for(const width of [390,1280]){await load(item.screen,item.query,width);await screenshot(`${item.name}-ru-${width}`);}
  for(const screen of ['place','cabinet'])for(const lang of ['az','en'])for(const width of [390,1280]){await load(screen,{lang,sample:'network',long:'1'},width);await screenshot(`${screen}-${lang}-long-${width}`);}
  assert.deepEqual(result.console_errors,[],'Console errors');assert.deepEqual(result.page_errors,[],'Runtime errors');assert.deepEqual(result.failed_resources,[],'Failed local resources');assert.deepEqual(result.external_requests,[],'External requests');
  result.status='PASS';
  console.log(`PASS: ${result.matrix.length} rendered matrix cases; ${result.flows.length} interaction flows; ${result.screenshots.length} screenshots; console/resource/external errors 0`);
})().catch(error=>{result.status='FAIL';result.failure=error.message;console.error('FAIL:',error.message);process.exitCode=1;}).finally(async()=>{fs.writeFileSync(path.join(out,'verification.json'),JSON.stringify(result,null,2)+'\n');if(browser)await browser.close();});
