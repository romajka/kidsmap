async page => {
await page.context().route('**/*',r=>r.request().url().startsWith('http://localhost:8811/')?r.continue():r.abort());
await page.goto('http://localhost:8811/ru/auth/login/');
await page.locator('input[name=username]').fill('owner@example.invalid');
await page.locator('input[type=password]').fill('__LOCAL_PASSWORD__');
await page.getByRole('button',{name:'Войти',exact:true}).click();
await page.goto('http://localhost:8811/ru/account/places/create/?type=permanent&fresh=1');
return {url:page.url(),inputs:await page.locator('input,select,textarea,button').evaluateAll(es=>es.map(e=>({tag:e.tagName,name:e.name,type:e.type,text:e.tagName==='BUTTON'?e.innerText:'',options:e.tagName==='SELECT'?Array.from(e.options).map(o=>({v:o.value,t:o.text})):undefined}))),body:(await page.locator('main').innerText()).slice(0,4500)};
}
