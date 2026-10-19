async original=>{
const browser=original.context().browser(),rows=[];
for(const c of browser.contexts())for(const p of c.pages())if(p.url().startsWith('http://127.0.0.1:33630/'))rows.push({url:p.url(),geometry:await p.evaluate(()=>({width:innerWidth,height:innerHeight,document_width:document.documentElement.scrollWidth,document_height:document.documentElement.scrollHeight,font_status:document.fonts.status,ready:document.readyState,buttons:[...document.querySelectorAll('button[name=_save],button[name=_continue]')].map(e=>({name:e.name,visible:e.getClientRects().length>0})),form_exists:!!document.querySelector('.km-settings-form-page')}))});
return{rows,scope:'Read-only diagnostic after screenshot timeout, no app or assertions changed'};
}
