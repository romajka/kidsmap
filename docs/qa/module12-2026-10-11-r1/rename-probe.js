async original=>{
__QA12_COMMON__
const{c,p}=await context('admin');await visit(p,'/admin/catalog/place/1/change/');const s=await shot(p,'place-before-rename-admin-1440');const form=await p.locator('form').evaluateAll(es=>es.map(e=>({action:e.action,fields:[...e.querySelectorAll('input,select,button')].filter(x=>['name_az','name_ru','name_en','status','_continue'].includes(x.name)).map(x=>({name:x.name,type:x.type,value:x.value,text:x.textContent?.slice(0,40)})),tabs:[...e.querySelectorAll('[data-pf-langtab]')].map(x=>({lang:x.dataset.pfLangtab,text:x.textContent}))})));await c.close();return{rows:[],form,shot:s};
}
