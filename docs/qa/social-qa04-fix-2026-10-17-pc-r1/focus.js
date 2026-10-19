async (page) => {
  const origin='http://127.0.0.1:33314',rows=[];
  for(const [lang,prefix] of [['ru','/ru'],['az',''],['en','/en']])for(const width of [390,1440]){
    await page.setViewportSize({width,height:844});await page.goto(origin+'/qa/login/invitation/');
    await page.goto(origin+prefix+'/account/notifications/');
    await page.locator('.account-nav-sidebar a').last().focus();await page.keyboard.press('Tab');
    const facts=await page.locator('.account-main-content button').first().evaluate(e=>{
      const s=getComputedStyle(e),nums=v=>v.match(/[\d.]+/g).map(Number),rgb=v=>nums(v).slice(0,3).map(n=>n/255);
      const lum=a=>a.map(n=>n<=.04045?n/12.92:((n+.055)/1.055)**2.4).reduce((a,n,i)=>a+n*[.2126,.7152,.0722][i],0);
      let p=e.parentElement,bg;while(p){bg=getComputedStyle(p).backgroundColor;if(nums(bg).length<4||nums(bg)[3]>0)break;p=p.parentElement;}
      const a=lum(rgb(s.outlineColor)),b=lum(rgb(bg));
      return {focused:document.activeElement===e,outlineColor:s.outlineColor,surrounding:bg,
        outlineWidth:parseFloat(s.outlineWidth),ratio:(Math.max(a,b)+.05)/(Math.min(a,b)+.05)};
    });
    rows.push({lang,width,facts,checks:{keyboard_focused:facts.focused,visible_outline:facts.outlineWidth>=2,focus_contrast:facts.ratio>=3}});
  }
  return rows;
}
