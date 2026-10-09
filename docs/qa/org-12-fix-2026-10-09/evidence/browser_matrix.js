async original => {
 const f={"organization": 69, "rows": [{"lang": "ru", "width": 360, "place": 113, "request": 103}, {"lang": "ru", "width": 390, "place": 114, "request": 104}, {"lang": "ru", "width": 768, "place": 115, "request": 105}, {"lang": "ru", "width": 1440, "place": 116, "request": 106}, {"lang": "az", "width": 360, "place": 117, "request": 107}, {"lang": "az", "width": 390, "place": 118, "request": 108}, {"lang": "az", "width": 768, "place": 119, "request": 109}, {"lang": "az", "width": 1440, "place": 120, "request": 110}, {"lang": "en", "width": 360, "place": 121, "request": 111}, {"lang": "en", "width": 390, "place": 122, "request": 112}, {"lang": "en", "width": 768, "place": 123, "request": 113}, {"lang": "en", "width": 1440, "place": 124, "request": 114}], "private": {"place": 109, "request": 98}, "old_rows": 565, "extra": {"cas": {"place": 110, "request": 100}, "nojs": {"place": 111, "request": 101}, "lost": {"place": 112, "request": 102}}, "first_attempt": [{"lang": "ru", "width": 360, "place": 97, "request": 86}, {"lang": "ru", "width": 390, "place": 98, "request": 87}, {"lang": "ru", "width": 768, "place": 99, "request": 88}, {"lang": "ru", "width": 1440, "place": 100, "request": 89}, {"lang": "az", "width": 360, "place": 101, "request": 90}, {"lang": "az", "width": 390, "place": 102, "request": 91}, {"lang": "az", "width": 768, "place": 103, "request": 92}, {"lang": "az", "width": 1440, "place": 104, "request": 93}, {"lang": "en", "width": 360, "place": 105, "request": 94}, {"lang": "en", "width": 390, "place": 106, "request": 95}, {"lang": "en", "width": 768, "place": 107, "request": 96}, {"lang": "en", "width": 1440, "place": 108, "request": 97}], "dashboard": "/account/places/"},base='http://localhost:8788',c=await original.context().browser().newContext(),p=await c.newPage(),rows=[],errors=[];
 const add=(id,ok)=>rows.push({id,status:ok?'PASS':'FAIL'});
 await c.route('**/*',r=>r.request().url().startsWith(base+'/')?r.continue():r.abort());p.on('pageerror',e=>errors.push(e.message));
 const login=async(role,page=p)=>{await page.goto(base+'/qa/');await page.getByRole('button',{name:'Войти: '+role,exact:true}).click();};
 for(const row of f.rows){
  const prefix=row.lang==='az'?'':'/'+row.lang,key=row.lang+'-'+row.width,url=base+prefix+'/account/organizations/'+f.organization+'/requests/'+row.request+'/recovery/';
  await login('demo_owner');await p.setViewportSize({width:row.width,height:1000});await p.goto(url);
  add(key+'-stale-screen',await p.locator('[data-join-recovery]').count()===1&&await p.locator('details').count()===1);
  add(key+'-language-heading',await p.getByRole('heading',{name:({ru:'Запрос на подключение',az:'Qoşulma sorğusu',en:'Connection request'})[row.lang],exact:true}).count()===1);
  add(key+'-no-overflow',await p.evaluate(()=>document.documentElement.scrollWidth<=innerWidth));
  await p.locator('summary').focus();await p.keyboard.press('Enter');add(key+'-keyboard-disclosure',await p.locator('details').getAttribute('open')!==null);
  await p.keyboard.press('Tab');add(key+'-keyboard-confirm-focus',await p.locator('[data-recovery-form] button').evaluate(e=>e===document.activeElement));
  if(row.width===390||row.width===1440)await p.screenshot({path:"/home/ramin/kidsmap/output/playwright/org12-fix-20261009"+'/before-'+key+'.png',fullPage:true});
  const response=p.waitForResponse(r=>r.url().includes('/cancel/')&&r.request().method()==='POST');await p.keyboard.press('Enter');add(key+'-cancel302',(await response).status()===302);await p.waitForURL(url);
  await p.locator('[data-recovery-result]').waitFor();add(key+'-result-focus',await p.locator('[data-recovery-result]').evaluate(e=>e===document.activeElement));
  add(key+'-separate-new-request',await p.getByRole('link',{name:({ru:'Создать новый запрос',az:'Yeni sorğu yarat',en:'Create new request'})[row.lang],exact:true}).count()===1);
  if(row.width===390||row.width===1440)await p.screenshot({path:"/home/ramin/kidsmap/output/playwright/org12-fix-20261009"+'/after-'+key+'.png',fullPage:true});
  await p.reload();add(key+'-canceled-reload',await p.locator('[data-recovery-result]').count()===1);
 }
 // UI creates one fresh request through the existing preview/consent process.
 const first=f.rows[0],prefix='/ru';await login('demo_owner');await p.goto(base+prefix+'/account/organizations/'+f.organization+'/connections/?q=ORG12+R2+ru+360');
 await p.locator('input[name="place_ids"][value="'+first.place+'"]').check();await p.locator('[data-preview]').click();
 await p.locator('input[name="consent"]').check();await p.locator('[data-confirm-form] button[type="submit"]').click();
 await p.waitForURL('**/account/organization-operations/**');add('new-preview-confirm-awaits-other',!(await p.locator('body').innerText()).includes('Request is stale'));
 // Private stale request is neutral, cancellation does not restore metadata visibility.
 await p.goto(base+'/ru/account/organizations/'+f.organization+'/requests/'+f.private.request+'/recovery/');add('private-name-redacted',!(await p.locator('body').innerText()).includes('ORG12 Private branch'));
 const a=await p.locator('input[name="expected_state"]').inputValue();
 const csrf=await p.locator('[data-recovery-form] input[name="csrfmiddlewaretoken"]').inputValue();
 const cancelUrl=base+'/ru/account/organizations/'+f.organization+'/requests/'+f.private.request+'/cancel/';
 const cancel=await c.request.post(cancelUrl,{form:{csrfmiddlewaretoken:csrf,expected_state:a},maxRedirects:0});add('private-cancel302',cancel.status()===302);
 const repeat=await c.request.post(cancelUrl,{form:{csrfmiddlewaretoken:csrf,expected_state:a},maxRedirects:0});add('private-repeat302',repeat.status()===302);
 await p.goto(base+'/ru/account/organizations/'+f.organization+'/requests/'+f.private.request+'/recovery/');add('private-no-new-link-network',await p.getByRole('link',{name:'Создать новый запрос',exact:true}).count()===0);
 await login('demo_outsider');await p.goto(base+'/ru/account/organizations/'+f.organization+'/requests/'+f.private.request+'/recovery/');add('private-place-owner-new-link',await p.getByRole('link',{name:'Создать новый запрос',exact:true}).count()===1);add('private-org-name-redacted',!(await p.locator('body').innerText()).includes('ORG12 Synthetic network'));
 // Both-side confirmation of the fresh public request from the owner's dashboard.
 await p.goto(base+'/ru/account/places/');
 // actual dashboard path supplied from fixture
 await p.goto(base+'/ru'+f.dashboard);
 const item=p.locator('[data-join-request]').filter({hasText:'ORG12 R2 ru 360'});add('place-dashboard-fresh-request',await item.count()===1);
 await item.getByRole('button',{name:'Подтвердить',exact:true}).click();await p.waitForLoadState('domcontentloaded');add('second-side-confirm-redirect',!p.url().includes('/confirm/'));
 await login('demo_manager');const forbidden=await p.goto(base+'/en/account/organizations/'+f.organization+'/requests/'+first.request+'/recovery/');add('employee404',forbidden.status()===404);
 await c.close();return {rows,errors};
}
