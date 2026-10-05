async page => {
 await page.setViewportSize({width:320,height:844});
 await page.goto('http://127.0.0.1:8780/admin/catalog/seoissue/');
 return page.evaluate(()=>Array.from(document.querySelectorAll('.content-wrapper div')).filter(e=>e.getBoundingClientRect().right>320&&e.getBoundingClientRect().width<320).slice(0,8).map(e=>({html:e.outerHTML.slice(0,400),parents:Array.from((function*(p){for(let i=0;p&&i<5;i++,p=p.parentElement)yield p;})(e)).map(p=>({tag:p.tagName,id:p.id,class:p.className,rect:{left:p.getBoundingClientRect().left,right:p.getBoundingClientRect().right},flex:getComputedStyle(p).flex,min:getComputedStyle(p).minWidth,overflow:getComputedStyle(p).overflowX}))})));
}
