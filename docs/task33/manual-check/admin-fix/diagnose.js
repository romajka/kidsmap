async page => {
 await page.getByRole('button',{name:'Войти: demo_moderator',exact:true}).click();
 await page.goto('http://127.0.0.1:8780/admin/catalog/organization/');
 await page.setViewportSize({width:1440,height:1000});
 await page.waitForLoadState('networkidle');
 await page.screenshot({path:'/mnt/c/kidsmap/output/playwright/manual-check/admin-organizations-before.png'});
 return await page.evaluate(()=>({
  url:location.pathname,title:document.title,
  headHeight:document.querySelector('#result_list thead')?.getBoundingClientRect().height,
  svg:Array.from(document.querySelectorAll('#result_list thead svg')).map(el=>({html:el.outerHTML,width:el.getBoundingClientRect().width,height:el.getBoundingClientRect().height,computed:{width:getComputedStyle(el).width,height:getComputedStyle(el).height}})),
  styles:Array.from(document.querySelectorAll('link[rel=stylesheet]')).map(el=>el.href),
  head:document.querySelector('#result_list thead')?.outerHTML,
  models:Array.from(document.querySelectorAll('.main-sidebar a[href]')).map(el=>({text:el.textContent.trim(),url:el.getAttribute('href')}))
 }));
}
