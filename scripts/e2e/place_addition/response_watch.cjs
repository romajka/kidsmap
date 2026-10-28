const assert=require('node:assert/strict');
function feedbackWatch(p,origin){
 const errors=[],unexpected=[],pending=[];let expectedChecks=0;
 p.on('pageerror',error=>errors.push(error.message));
 p.on('response',response=>{if(!response.url().startsWith(origin)||response.status()<400)return;
  pending.push((async()=>{const request=response.request(),data=request.postData()||'',url=new URL(response.url());
   const checkOnly=/name="_km_check_required"\r?\n\r?\n1(?:\r?\n|$)/.test(data)||new URLSearchParams(data).get('_km_check_required')==='1';
   if(response.status()===422&&request.method()==='POST'&&/\/account\/places\/(?:\d+\/)?preview\/$/.test(url.pathname)&&checkOnly){
    try{const payload=await response.json(),r=payload.readiness;
     if(payload.errors&&typeof payload.errors==='object'&&!Array.isArray(payload.errors)&&Object.keys(payload.errors).length&&r&&r.is_ready===false&&Array.isArray(r.items)&&Array.isArray(r.sections)&&Number.isInteger(r.required_count)&&Number.isInteger(r.completed_count)&&r.completed_count>=0&&r.completed_count<=r.required_count){expectedChecks++;return;}
    }catch{}
   }
   unexpected.push({url:response.url(),status:response.status(),method:request.method(),checkOnly});
  })());
 });
 return {errors,async verify(){await Promise.all(pending);assert.deepEqual(unexpected,[],'Only contracted incomplete check-only 422 responses are expected');return expectedChecks;}};
}
module.exports={feedbackWatch};
