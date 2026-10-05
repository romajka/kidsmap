async page => {
 await page.goto('http://127.0.0.1:8780/admin/catalog/place/');
 const rows=await page.locator('#result_list tbody tr').first().evaluate(e=>({height:e.getBoundingClientRect().height,cells:Array.from(e.children).map(c=>({class:c.className,height:c.getBoundingClientRect().height,width:c.getBoundingClientRect().width,display:getComputedStyle(c).display})),images:Array.from(e.querySelectorAll('img,svg')).map(i=>({tag:i.tagName,class:i.getAttribute('class'),height:i.getBoundingClientRect().height,width:i.getBoundingClientRect().width,css:getComputedStyle(i).height}))}));
 await page.screenshot({path:'/mnt/c/kidsmap/output/playwright/manual-check/admin-place-final-mobile.png'});
 return rows;
}
