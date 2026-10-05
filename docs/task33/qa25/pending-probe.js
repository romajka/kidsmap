async(page)=>{
const rows=[],checks=[],events={errors:[],failed:[],staticFailures:[],external:[]};
page.on('pageerror',e=>events.errors.push(String(e)));
for(const lang of ['az','ru','en']){
 await page.goto('http://127.0.0.1:8795/docs/task33/design/specialist/profile.html?lang='+lang+'&state=pending',{waitUntil:'networkidle'});
 const count=await page.locator('[data-action="certificate"]').count();
 rows.push({file:'profile.html',lang,width:1280,issues:count?['pending_certificate_public']:[]});
 checks.push({check:'pending_certificate_not_public',lang,pass:count===0});
}
return{rows,total:rows.length,passed:rows.filter(r=>!r.issues.length).length,checks,checksPassed:checks.filter(c=>c.pass).length,events};
}
