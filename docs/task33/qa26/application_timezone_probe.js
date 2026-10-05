async(page)=>{
 const browser=page.context().browser();if(!browser)throw new Error('Actual independent UTC context unavailable');
 const context=await browser.newContext({timezoneId:'UTC'});const other=await context.newPage();
 const timezone=await other.evaluate(()=>Intl.DateTimeFormat().resolvedOptions().timeZone);await context.close();
 if(timezone!=='UTC')throw new Error('Actual UTC override failed');return {browser:true,timezone};
}
