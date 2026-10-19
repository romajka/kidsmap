async page=>{
 const B='http://127.0.0.1:33780',rows=[],errors=[];
 try{
  await page.goto(B+'/qa/m12/login/admin/');
  for(const lang of ['az','ru','en'])for(const width of [360,1440]){
   await page.context().addCookies([{name:'django_language',value:lang,domain:'127.0.0.1',path:'/'}]);await page.setViewportSize({width,height:900});await page.goto(B+'/admin/catalog/siteanalytics/');
   const geometry=await page.locator('.km-kpi-card').evaluateAll(cards=>cards.map(card=>{const c=card.getBoundingClientRect(),l=card.querySelector('.km-kpi-card__label').getBoundingClientRect(),i=card.querySelector('.km-kpi-card__icon').getBoundingClientRect();return{fits:i.right<=c.right-8&&l.right<=i.left-4,labelRight:l.right,iconLeft:i.left,iconRight:i.right,cardRight:c.right}}));
   rows.push({id:'kpi-fit-'+lang+'-'+width,lang,width,checks:{card_contents_fit:geometry.every(g=>g.fits)},geometry});
  }
 }catch(e){errors.push(String(e))}return{rows,errors};
}
