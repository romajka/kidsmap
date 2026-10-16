async(original)=>{
const B='__BASE__',F=__FIXTURES__,HERE='__HERE__',rows=[],errors=[],network=[],blocked=[];let phase='start';const c=await original.context().browser().newContext();
const check=(id,ok,detail={})=>{rows.push({id,status:ok?'PASS':'FAIL',detail});if(!ok)throw Error(id);};
await c.route('**/*',r=>r.request().url().startsWith(B)||r.request().url().startsWith('data:')?r.continue():(blocked.push(r.request().url().split('?')[0]),r.abort()));const p=await c.newPage();p.setDefaultTimeout(10000);p.on('pageerror',e=>errors.push(e.message));p.on('response',r=>{if(r.url().startsWith(B)&&r.status()>=400)network.push({url:r.url().split('?')[0],status:r.status()});});
const EXPECT={ru:{primary:'Основной',addon:'Дополнительный',registration_fee:'Регистрационный взнос',one_time:'Разовая оплата',recurring:'Регулярная оплата',installment:'Оплата частями'},az:{primary:'Əsas',addon:'Əlavə',registration_fee:'Qeydiyyat haqqı',one_time:'Birdəfəlik ödəniş',recurring:'Müntəzəm ödəniş',installment:'Hissə-hissə ödəniş'},en:{primary:'Primary',addon:'Additional',registration_fee:'Registration fee',one_time:'One-time payment',recurring:'Recurring payment',installment:'Payment in installments'}};
async function open(d){if(await d.getAttribute('open')===null)await d.locator(':scope > summary').click();}
async function editor(cell){await p.goto(B+'/'+cell.lang+'/account/places/'+cell.place+'/edit/?fresh=1');await p.waitForLoadState('networkidle');await p.reload();await p.waitForLoadState('networkidle');const a=p.locator('[data-pc-offerings] .pc-activity-card').first();await open(a);const g=a.locator('.pc-group-card').first();await open(g);const pl=g.locator('.pc-plan-card').first();await open(pl);await open(pl.locator('details').first());return pl;}
const field=(pl,key)=>pl.locator('[data-offering-key='+key+']');
try{
phase='login';await p.goto(B+'/ru/auth/login/');await p.locator('[name=username]').fill(F.owner_email);await p.locator('[name=password]').fill('__PASSWORD__');await Promise.all([p.waitForURL(u=>!u.pathname.includes('login')),p.locator('button[data-loading-button]').click()]);
for(const cell of F.owner_cells.filter(x=>x.lang==='en')){
for(const width of []){
 phase=cell.lang+'-'+width;await p.setViewportSize({width,height:950});let pl=await editor(cell);const expected=EXPECT[cell.lang];
 for(const [key,codes] of [['charge_role',['primary','addon','registration_fee']],['billing_mode',['one_time','recurring','installment']],['product_type',['registration_fee']]]){
 const f=field(pl,key);check(phase+'-'+key+'-visible',await f.isVisible());
 for(const code of codes){const text=await f.locator('option[value='+code+']').textContent();check(phase+'-'+key+'-'+code,text===expected[code],{text,value:code});}
 await f.click();await p.keyboard.press('Escape');check(phase+'-'+key+'-native-focus',await f.evaluate(e=>document.activeElement===e));
 }
 const geom=await pl.evaluate(e=>({right:e.getBoundingClientRect().right,width:e.getBoundingClientRect().width,viewport:innerWidth,documentOverflow:document.documentElement.scrollWidth>innerWidth}));check(phase+'-geometry',!geom.documentOverflow&&geom.right<=geom.viewport+1,geom);
 await p.screenshot({path:HERE+'/screenshots/owner-'+phase+'.png',fullPage:true});
}
phase=cell.lang+'-canonical-reload';await p.setViewportSize({width:390,height:950});let pl;
pl=await editor(cell);const actual={};for(const k of ['billing_mode','charge_role','product_type','billing_interval_count','title_az'])actual[k]=await field(pl,k).inputValue();check(cell.lang+'-settled-normal-reload-code-values',await field(pl,'billing_mode').inputValue()==='recurring'&&await field(pl,'charge_role').inputValue()==='registration_fee'&&await field(pl,'product_type').inputValue()==='registration_fee'&&await field(pl,'billing_interval_count').inputValue()==='2'&&await field(pl,'title_az').inputValue()==='Uydurma OFFER06 '+cell.lang+' native',actual);await p.screenshot({path:HERE+'/screenshots/owner-'+cell.lang+'-save-reload.png',fullPage:true});
}
check('owner-no-pageerrors',errors.length===0,{errors});return{rows,errors,network,blocked:[...new Set(blocked)]};
}catch(e){return{rows,error:String(e),phase,errors,network,blocked:[...new Set(blocked)]};}finally{await c.close();}
}
