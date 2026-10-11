async original=>{
 const F={
  "actors": {
    "owner": {
      "id": 1,
      "username": "qa10_owner",
      "email": "owner10@example.invalid"
    },
    "staff": {
      "id": 2,
      "username": "qa10_staff",
      "email": "staff10@example.invalid"
    },
    "admin": {
      "id": 3,
      "username": "qa10_admin",
      "email": "admin10@example.invalid"
    },
    "outsider": {
      "id": 4,
      "username": "qa10_outsider",
      "email": "outsider10@example.invalid"
    }
  },
  "places": {
    "live": 1,
    "draft": 2,
    "inactive": 3,
    "archived": 4,
    "deleted": 5
  },
  "specialist": 1,
  "event": 1,
  "organization": 1,
  "organization_public_id": "6911adc9-9ea0-4fc9-8112-e06ce2db1238",
  "urls": {
    "ru": {
      "place": "/ru/place/1-vymyshlennoe-qa10-live/",
      "specialist": "/ru/specialists/fictional-qa10-specialist/",
      "event": "/ru/event/1-uydurma-qa10-tedbir/",
      "organization": "/ru/organizations/6911adc9-9ea0-4fc9-8112-e06ce2db1238/"
    },
    "az": {
      "place": "/place/1-uydurma-qa10-live/",
      "specialist": "/specialists/fictional-qa10-specialist/",
      "event": "/event/1-uydurma-qa10-tedbir/",
      "organization": "/organizations/6911adc9-9ea0-4fc9-8112-e06ce2db1238/"
    },
    "en": {
      "place": "/en/place/1-fictional-qa10-live/",
      "specialist": "/en/specialists/fictional-qa10-specialist/",
      "event": "/en/event/1-uydurma-qa10-tedbir/",
      "organization": "/en/organizations/6911adc9-9ea0-4fc9-8112-e06ce2db1238/"
    }
  },
  "settings": 1,
  "synthetic_only": true
},B='http://localhost:8823',c=await original.context().browser().newContext({viewport:{width:1440,height:950}});
 await c.route('**/*',r=>new URL(r.request().url()).hostname==='localhost'?r.continue():r.abort());const p=await c.newPage();
 await p.goto(B+'/ru/auth/login/');await p.locator('input[name=username]').fill(F.actors.admin.email);await p.locator('input[name=password]').fill('__LOCAL_PASSWORD__');await p.locator('.register-form--login button[type=submit]').click();await p.waitForTimeout(300);
 const sr=await p.request.get(B+'/qa/state/');const st=await sr.text();if(sr.status()!==200)return{stateError:sr.status(),reason:st.match(/<pre class="exception_value">([\s\S]*?)<\/pre>/)?.[1]};const output={state:JSON.parse(st),pages:[]};
 for(const path of ['/admin/catalog/sitesettings/','/admin/catalog/sitebrandingsettings/1/change/','/admin/catalog/sitevisibilitysettings/1/change/','/admin/catalog/sitegalleryimage/','/ru/','/ru/about/','/ru/contacts/','/ru/catalog/?q=QA10-NO-MATCH']){
  const response=await p.goto(B+path);await p.waitForTimeout(150);
  output.pages.push({path,url:p.url(),status:response.status(),head:(await p.locator('body').innerText()).slice(0,1200),fields:await p.locator('input:not([type=hidden]),textarea,select').evaluateAll(es=>es.map(e=>({tag:e.tagName,type:e.type,name:e.name,id:e.id}))),buttons:await p.locator('button').evaluateAll(es=>es.map(e=>({text:e.innerText,name:e.name,type:e.type,cls:e.className}))),imageInputs:await p.locator('input[type=file]').evaluateAll(es=>es.map(e=>({name:e.name,field:e.dataset.field,placement:e.dataset.placement,html:e.outerHTML})))});
 }
 await c.close();return output;
}
