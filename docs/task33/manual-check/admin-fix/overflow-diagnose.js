async page => {
 const rows=[];
 await page.setViewportSize({width:390,height:844});
 for(const path of ['/admin/catalog/place/?is_temporary__exact=0','/admin/catalog/staffaccessuser/','/admin/catalog/seoissue/']){
  await page.goto('http://127.0.0.1:8780'+path);await page.waitForLoadState('networkidle');
  const data=await page.evaluate(()=>{
   const nodes=Array.from(document.querySelectorAll('.content-wrapper *, .main-header *'));
   return {width:innerWidth,scrollWidth:document.documentElement.scrollWidth,elements:nodes.filter(e=>{
    const r=e.getBoundingClientRect();if(r.right<=innerWidth||r.width===0)return false;
    for(let p=e.parentElement;p&&p!==document.body;p=p.parentElement){if(['auto','scroll','hidden','clip'].includes(getComputedStyle(p).overflowX)&&p.getBoundingClientRect().right<=innerWidth)return false;}
    return true;
   }).slice(0,35).map(e=>({tag:e.tagName,id:e.id,class:e.className,right:e.getBoundingClientRect().right,width:e.getBoundingClientRect().width,
     css:{display:getComputedStyle(e).display,width:getComputedStyle(e).width,minWidth:getComputedStyle(e).minWidth,overflow:getComputedStyle(e).overflowX,flex:getComputedStyle(e).flex},parent:e.parentElement.className}))};
  });rows.push({path,...data});
  await page.screenshot({path:'/mnt/c/kidsmap/output/playwright/manual-check/admin-'+(path.includes('staff')?'staff':path.includes('seo')?'seo':'places')+'-overflow-after.png'});
 }
 return rows;
}
