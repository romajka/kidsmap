from pathlib import Path
O=Path('/mnt/c/kidsmap/docs/qa/module11-repair-2026-10-18-pc-r1');t=(O/'browser-identity-r2.js').read_text();old="await p.locator('#id_name').fill(name);";assert t.count(old)==1;t=t.replace(old,old+"const options=p.locator('#id_specializations input[type=checkbox]');if(await options.filter({checked:true}).count()===0)await options.first().check();")
# Locator.filter has no checked option: use the actual checked DOM selector.
t=t.replace("await options.filter({checked:true}).count()", "await p.locator('#id_specializations input[type=checkbox]:checked').count()")
t=t.replace('return(await post).status();',"const response=await post;if(response.status()!==302)throw Error('Native save rejected: '+JSON.stringify(await p.locator('.km-error-banner,.errorlist').allTextContents()));return response.status();")
t=t.replace('No ORM transitions, forged DOM fields or modified transport.', 'Initial fixture lacked required specialization; first actual save chooses an existing native checkbox, retained as one owned synthetic relation. Original names/slug/paths/media restored; no ORM transitions, forged DOM fields or modified transport.')
(O/'browser-identity-r3.js').write_text(t)
