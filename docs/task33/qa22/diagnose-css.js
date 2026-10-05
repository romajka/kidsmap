async(page)=>{
const rules=['.km-place-section{min-width:0}','.km-place-form-main{min-width:0;grid-template-columns:minmax(0,1fr)}','.km-place-section .form-group{min-width:0}','.km-place-section .readonly{overflow-wrap:anywhere;word-break:break-word}','.km-place-section{min-width:0}.km-place-section .form-group{min-width:0}.km-place-section .readonly{overflow-wrap:anywhere;word-break:break-word}'];
return await page.evaluate(rules=>{
 const result={url:location.pathname,viewport:innerWidth,baseline:document.documentElement.scrollWidth,selectors:[],variants:[]};
 for(const selector of['.km-place-form-main','.km-place-section','.km-place-section__body','.field-version_history','.field-version_history .readonly']){
  const node=document.querySelector(selector),s=getComputedStyle(node),r=node.getBoundingClientRect();
  result.selectors.push({selector,width:r.width,right:r.right,minWidth:s.minWidth,display:s.display,columns:s.gridTemplateColumns,overflowWrap:s.overflowWrap});
 }
 for(const rule of rules){const style=document.createElement('style');style.textContent=rule;document.head.append(style);result.variants.push({rule,scrollWidth:document.documentElement.scrollWidth});style.remove();}
 result.restored=document.documentElement.scrollWidth;return result;
},rules);
}
