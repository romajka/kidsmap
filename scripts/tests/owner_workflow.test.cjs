const test=require('node:test'),assert=require('node:assert/strict'),fs=require('node:fs');
const {JSDOM}=require(process.env.KIDSMAP_JSDOM||'jsdom');
function mount(setup=()=>{}){
 const readiness={items:[{code:'name',field:'name_az',complete:false,config:{}},{code:'price',field:'pricing_plans',complete:false,config:{}}],required_count:2,completed_count:0,is_ready:false};
 const d=new JSDOM(`<html lang="ru"><div data-place-mode="continuous"><script id="pw-copy" type="application/json">{"empty":"Не заполнено"}</script><script id="pc-readiness" type="application/json">${JSON.stringify(readiness)}</script><script id="pc-draft-fields" type="application/json">["name_az","pricing_plans"]</script><form data-permanent-place-form data-fresh="1" data-account-id="1" data-schema-version="1" data-source-version="0" data-draft-key="test" data-draft-url="/drafts/"><input name="csrfmiddlewaretoken" value="test"><input name="draft_client_key" value="test"><input name="server_draft_id"><input name="name_az"><input name="age_open_ended"><input name="pricing_plans" value="[]"><span data-pc-lifecycle></span><p data-pc-save-status></p><p data-pc-conflict-actions hidden><a></a></p><p data-pc-readiness-status></p><span data-pc-ready-count></span><div data-pc-progress-fill></div><span data-pc-progress-pct></span><div data-tariff-list><div>Invalid empty tariff</div></div><select data-pc-section-select></select>${[1,2,3,4].map(i=>`<span data-pc-step-badge="${i}"></span><span data-pc-section-tag="${i}"></span>`).join('')}${['description','name','address','offerings','price'].map(n=>`<span data-pc-preview-${n}></span>`).join('')}<button type="submit" data-km-preview formaction="/preview/" formtarget="_blank">Preview</button><button type="submit" data-pc-save-draft name="form_action" value="save_draft">Save</button><a href="/account/places/" id="leave">Leave</a></form></div></html>`,{url:'http://localhost/create/',runScripts:'outside-only',pretendToBeVisual:true});
 const w=d.window;w.matchMedia=()=>({matches:true});w.HTMLElement.prototype.scrollIntoView=()=>{};w.fetch=async()=>({ok:true,json:async()=>({drafts:[]})});setup(w);w.eval(fs.readFileSync('static/js/owner_place_continuous.js','utf8'));return d;
}
test('initial empty progress is zero and an invalid tariff row cannot complete prices',()=>{const d=mount(),doc=d.window.document;assert.equal(doc.querySelector('[data-pc-progress-fill]').style.width,'0%');assert.notEqual(doc.querySelector('[data-pc-step-badge="3"]').dataset.status,'complete');d.window.close();});

test('unchanged readiness retains requirement controls and their keyboard focus',()=>{
 const d=mount(w=>{const list=w.document.createElement('ul');list.dataset.pcRequirementsList='';w.document.querySelector('form').append(list);});
 try{const w=d.window,list=w.document.querySelector('[data-pc-requirements-list]'),button=list.querySelector('button');button.focus();
 for(let i=0;i<8;i++)w.KidsMapOwnerWorkflow.invalidateReadiness();
 assert.equal(list.querySelector('button'),button,'pending checks must not rebuild unchanged requirements');assert.equal(w.document.activeElement,button);
 }finally{d.window.close();}
});

test('a save-panel resize never drags the page back to an offscreen active field',async()=>{
 let resize,rect={top:150,bottom:190,left:100,right:300,width:200,height:40},scrolls=0;
 const d=mount(w=>{const bar=w.document.createElement('div');bar.className='pc-savebar';w.document.querySelector('form').append(bar);
 w.ResizeObserver=class{constructor(callback){resize=callback;}observe(){}};
 w.document.querySelector('[name=name_az]').getBoundingClientRect=()=>rect;w.scrollBy=()=>scrolls++;
 });
 try{const w=d.window;w.document.querySelector('[name=name_az]').focus();await new Promise(r=>setTimeout(r,25));scrolls=0;
 rect={...rect,top:-600,bottom:-560};resize?.([]);await new Promise(r=>setTimeout(r,25));
 assert.equal(scrolls,0,'background UI changes must not override manual scrolling');
 }finally{d.window.close();}
});

test('failed saving shows one recovery action without stacking a saved link beside retry',async()=>{
 const d=mount(w=>{const f=w.document.querySelector('form');f.insertAdjacentHTML('beforeend','<a data-pc-saved-link hidden>Drafts</a><button type="button" data-pc-save-retry hidden>Retry</button>');w.fetch=async()=>{throw Error('lost network');};});
 try{assert.equal(await d.window.KidsMapOwnerWorkflow.save(),false);assert.equal(d.window.document.querySelector('[data-pc-save-retry]').hidden,false);assert.equal(d.window.document.querySelector('[data-pc-saved-link]').hidden,true);}
 finally{d.window.close();}
});
test('server progress replaces totals without tariff DOM heuristics',async()=>{const d=mount(),w=d.window;assert(w.KidsMapOwnerWorkflow);const result={required_count:2,completed_count:1,is_ready:false,items:[],sections:[{id:1,required_count:1,completed_count:1,is_complete:true,error_count:0},{id:2,required_count:0,completed_count:0,is_complete:true,error_count:0},{id:3,required_count:1,completed_count:0,is_complete:false,error_count:0},{id:4,required_count:0,completed_count:0,is_complete:true,error_count:0}]};w.KidsMapOwnerWorkflow.setReadiness(result);assert.equal(w.document.querySelector('[data-pc-progress-pct]').textContent,'50%');assert.equal(w.document.querySelector('[data-pc-step-badge="1"]').textContent,'1/1');d.window.close();});

test('a response for older form values cannot mark newer edits ready',async()=>{const d=mount(),w=d.window;let answer;w.fetch=()=>new Promise(resolve=>answer=resolve);const pending=w.KidsMapOwnerWorkflow.checkReadiness();w.KidsMapOwnerWorkflow.invalidateReadiness();answer({ok:true,status:200,json:async()=>({readiness:{required_count:2,completed_count:2,is_ready:true,items:[],sections:[]}})});await pending;assert.equal(w.document.querySelector('[data-pc-progress-pct]').textContent,'0%');w.close();});
test('failed private save keeps the page dirty and does not claim saved',async()=>{const d=mount(),w=d.window;w.fetch=async()=>{throw Error('offline')};assert.equal(await w.KidsMapOwnerWorkflow.save(),false);assert(w.KidsMapOwnerWorkflow.hasPending());assert.equal(w.document.querySelector('[data-pc-save-status]').dataset.state,'error');const e=new w.Event('beforeunload',{cancelable:true});assert.equal(w.dispatchEvent(e),false);w.close();});
test('navigation offers private save but a preview in another tab does not prompt',async()=>{const d=mount(),w=d.window;w.fetch=async()=>{throw Error('network')};await w.KidsMapOwnerWorkflow.save();let options;w.kmModal={unsavedChanges:o=>options=o};const e=new w.MouseEvent('click',{button:0,bubbles:true,cancelable:true});w.document.querySelector('#leave').dispatchEvent(e);assert(e.defaultPrevented);assert.equal(typeof options.onSaveAndExit,'function');assert.equal(typeof options.onExitWithoutSaving,'function');const link=w.document.createElement('a');link.href='/preview/';link.target='_blank';w.document.body.append(link);options=null;link.dispatchEvent(new w.MouseEvent('click',{button:0,bubbles:true,cancelable:true}));assert.equal(options,null);w.close();});


test('signed server copy restores structured editors through input events',async()=>{
 let inputs=0, schedules=0;
 const d=mount(w=>{const f=w.document.querySelector('form');f.dataset.fresh='0';f.dataset.baseSignature='base';w.document.getElementById('pc-draft-fields').textContent='["name_az","pricing_plans","structured_schedule"]';const schedule=w.document.createElement('input');schedule.name='structured_schedule';f.append(schedule);schedule.addEventListener('km:schedule-import',()=>schedules++);w.history.replaceState(null,'','?draft_id=saved');
 f.elements.pricing_plans.addEventListener('input',()=>inputs++);
 w.fetch=async()=>({ok:true,status:200,json:async()=>({draft_id:'saved',version:2,target_type:'place',target_id:null,schema_version:1,source_version:0,saved_at:new Date().toISOString(),fields:{structured_schedule:[{day:0}],name_az:'Restored',pricing_plans:[{kind:'entry'}],_editor_base_signature:'base'},media_manifest:[]})});});
 await new Promise(r=>setTimeout(r,15));assert.equal(d.window.document.querySelector('[name=name_az]').value,'Restored');assert.equal(inputs,1);assert.equal(schedules,1);d.window.close();
});

test('cabinet discard requires confirmation and preserves the card on conflict',async()=>{
 const d=new JSDOM('<html lang="ru"><input name="csrfmiddlewaretoken" value="csrf"><article data-working-draft-id="id"><button data-working-draft-delete data-url="/api/drafts/id/" data-version="7">Delete</button><p data-working-draft-error></p></article></html>',{url:'http://localhost/',runScripts:'outside-only'}),w=d.window;
 let calls=0,allow=false;w.kmModal={confirm:async()=>allow};w.fetch=async(url,options)=>{calls++;assert.equal(options.method,'DELETE');assert.deepEqual(JSON.parse(options.body),{expected_version:7});assert.equal(options.headers['X-CSRFToken'],'csrf');return {ok:false,status:409};};
 w.eval(fs.readFileSync('static/js/owner_working_drafts.js','utf8'));const button=w.document.querySelector('button');button.click();await new Promise(r=>setTimeout(r,0));assert.equal(calls,0);allow=true;button.click();await new Promise(r=>setTimeout(r,0));assert.equal(calls,1);assert(w.document.querySelector('article'));assert.match(w.document.querySelector('[data-working-draft-error]').textContent,/измен/);assert.equal(button.disabled,false);w.close();
});

test('failed draft restoration cannot overwrite saved media on retry',async()=>{
 let readable=false,posts=0,restores=0;
 const detail={draft_id:'saved',version:2,target_type:'place',target_id:null,schema_version:1,source_version:0,saved_at:new Date().toISOString(),fields:{name_az:'Restored'},media_manifest:[{id:'photo',role:'main'}]};
 const d=mount(w=>{const f=w.document.querySelector('form');f.dataset.fresh='0';w.history.replaceState(null,'','?draft_id=saved');
 w.KidsMapDraftMedia={mount:()=>({restore:async data=>{assert.equal(data.media_manifest.length,1);restores++;},save:async data=>data,hasPending:()=>false})};
 w.fetch=async(url,options)=>{if(options?.method==='POST'){posts++;return {ok:true,json:async()=>detail};}if(!readable)throw Error('offline');return {ok:true,status:200,json:async()=>detail};};});
 await new Promise(r=>setTimeout(r,5));assert.equal(await d.window.KidsMapOwnerWorkflow.save(),false);assert.equal(posts,0);readable=true;assert.equal(await d.window.KidsMapOwnerWorkflow.save(),true);assert.equal(restores,1);assert.equal(posts,1);d.window.close();
});

test('explicit filled save uses native private materialization and blank save remains a working copy',async()=>{
 let native=0, drafts=0;
 const d=mount(w=>{const f=w.document.querySelector('form'),category=w.document.createElement('input');category.name='category';category.value='EDU';f.append(category);f.elements.name_az.value='Named';
 w.KidsMapPhotoEditor={mount:()=>({save:async()=>{native++;return {ok:false,errors:{}};}})};
 w.fetch=async()=>{drafts++;return {ok:false,status:400,json:async()=>({})};};});
 const w=d.window,f=w.document.querySelector('form'),button=f.querySelector('[data-pc-save-draft]');f.dispatchEvent(new w.SubmitEvent('submit',{bubbles:true,cancelable:true,submitter:button}));await new Promise(r=>setTimeout(r,5));assert.equal(native,1);assert.equal(drafts,0);f.elements.name_az.value='';f.dispatchEvent(new w.SubmitEvent('submit',{bubbles:true,cancelable:true,submitter:button}));await new Promise(r=>setTimeout(r,5));assert.equal(native,1);assert.equal(drafts,1);w.close();
});

test('lightweight readiness excludes new gallery order without uploading files',async()=>{
 const d=mount(w=>{const input=w.document.createElement('input');input.name='gallery_order';input.value='["new:0"]';w.document.querySelector('form').append(input);});
 let body;d.window.fetch=async(url,options)=>{body=options.body;return {ok:true,status:200,json:async()=>({})};};await d.window.KidsMapOwnerWorkflow.checkReadiness();assert.equal(body.has('gallery_order'),false);d.window.close();
});

test('refresh warns while a text save is still in flight',async()=>{
 const d=mount(),w=d.window;let answer;w.fetch=()=>new Promise(r=>answer=r);const pending=w.KidsMapOwnerWorkflow.save();const event=new w.Event('beforeunload',{cancelable:true});assert.equal(w.dispatchEvent(event),false);await Promise.resolve();answer({ok:false,status:503,json:async()=>({})});await pending;w.close();
});

test('restored pending media is not announced as fully saved',async()=>{
 const d=mount(w=>{const f=w.document.querySelector('form');f.dataset.fresh='0';w.history.replaceState(null,'','?draft_id=pending');w.KidsMapDraftMedia={mount:()=>({restore:async()=>{},hasPending:()=>true})};w.fetch=async()=>({ok:true,status:200,json:async()=>({draft_id:'pending',version:3,target_type:'place',target_id:null,schema_version:1,source_version:0,saved_at:new Date().toISOString(),fields:{name_az:'Pending upload'},media_manifest:[]})});});
 await new Promise(r=>setTimeout(r,10));assert(d.window.KidsMapOwnerWorkflow.hasPending());assert.notEqual(d.window.document.querySelector('[data-pc-save-status]').dataset.state,'saved');d.window.close();
});

test('a missing celebration asset keeps the visible welcome mascot',()=>{
 const d=mount(w=>{const mascot=w.document.createElement('div');mascot.dataset.pcMappy='';mascot.dataset.welcome='/welcome.webp';mascot.dataset.success='/success.webp';mascot.innerHTML='<img><p></p>';w.document.querySelector('form').append(mascot);});
 d.window.KidsMapOwnerWorkflow.setReadiness({items:[],sections:[],required_count:1,completed_count:1,is_ready:true});const image=d.window.document.querySelector('[data-pc-mappy] img');image.dispatchEvent(new d.window.Event('error'));assert.equal(image.getAttribute('src'),'/welcome.webp');d.window.close();
});

test('text autosave preserves intended media IDs and roles before upload completes',async()=>{
 let saved;
 const d=mount(w=>{w.KidsMapPhotoEditor={mount:()=>({snapshotMedia:()=>[{id:'asset-id',role:'main',order:0,file:{name:'x.webp'}}]})};w.fetch=async(url,options)=>{saved=JSON.parse(options.body);return {ok:false,status:503,json:async()=>({})};};});
 await d.window.KidsMapOwnerWorkflow.save();assert.deepEqual(saved.fields._draft_media_selection,[{id:'asset-id',role:'main',order:0}]);d.window.close();
});

test('lost text response retries the identical UUID/version before newer edits',async()=>{
 const calls=[];const d=mount(w=>{w.fetch=async(url,options)=>{const body=JSON.parse(options.body);calls.push(body);if(calls.length===1)throw Error('lost response');return {ok:true,json:async()=>({draft_id:body.draft_id,version:calls.length-1,saved_at:new Date().toISOString()})};};});
 assert.equal(await d.window.KidsMapOwnerWorkflow.save(),false);d.window.document.querySelector('[name=name_az]').value='Newer';assert.equal(await d.window.KidsMapOwnerWorkflow.save(),true);assert(calls[0].draft_id);assert.deepEqual(calls[1],calls[0]);assert.equal(calls[2].fields.name_az,'Newer');d.window.close();
});
test('lost media response is resolved before the next text version is sent',async()=>{
 const order=[];let count=0;const d=mount(w=>{w.KidsMapDraftMedia={mount:()=>({hasPending:()=>false,save:async(result,adopt)=>{count++;order.push('media');if(count===1)throw Error('lost media response');const next={...result,version:result.version+1};adopt(next);return next;}})};w.fetch=async(url,options)=>{order.push('text');const body=JSON.parse(options.body);return {ok:true,json:async()=>({draft_id:body.draft_id,version:body.expected_version+1,saved_at:new Date().toISOString()})};};});
 assert.equal(await d.window.KidsMapOwnerWorkflow.save(),false);assert.equal(await d.window.KidsMapOwnerWorkflow.save(),true);assert.deepEqual(order.slice(0,4),['text','media','media','text']);d.window.close();
});

test('native form carries the confirmed draft version after text and media saves',async()=>{
 const d=mount(w=>{w.KidsMapDraftMedia={mount:()=>({hasPending:()=>false,save:async(result,adopt)=>{const next={...result,version:4};adopt(next);return next;}})};w.fetch=async(url,options)=>({ok:true,json:async()=>({draft_id:JSON.parse(options.body).draft_id,version:1,saved_at:new Date().toISOString()})});});
 assert.equal(await d.window.KidsMapOwnerWorkflow.save(),true);assert.equal(d.window.document.querySelector('[name=server_draft_version]')?.value,'4');d.window.close();
});
