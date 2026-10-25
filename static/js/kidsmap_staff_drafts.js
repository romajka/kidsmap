/* Actor-private working copies for the admin and volunteer place editors. */
(() => {
  'use strict';
  function init() {
    const node=document.getElementById('km-staff-draft-config');if(!node)return;
    let config;try{config=JSON.parse(node.textContent);}catch{return;}
    const form=document.querySelector('#place_form, #volunteer-place-form, form[data-volunteer-form]') || document.querySelector('form[enctype="multipart/form-data"]');
    if(!form||!config.collectionUrl||form.kmDraftSave)return;
    const language=(document.documentElement.lang||'az').split('-')[0];
    const copy={ru:{initial:'Автосохранение включено',dirty:'Есть несохранённые изменения',saving:'Сохраняем черновик…',saved:'Черновик сохранён',failed:'Не удалось сохранить. Изменения остаются в форме.',conflict:'Карточка изменилась. Откройте актуальную версию перед продолжением.',restore:'Восстанавливаем черновик и фотографии…',retry:'Повторить',list:'Мои черновики'},en:{initial:'Autosave is on',dirty:'You have unsaved changes',saving:'Saving draft…',saved:'Draft saved',failed:'Could not save. Your changes remain in this form.',conflict:'This card has changed. Open the current version before continuing.',restore:'Restoring draft and photos…',retry:'Retry',list:'My drafts'},az:{initial:'Avtomatik saxlama aktivdir',dirty:'Saxlanılmamış dəyişikliklər var',saving:'Qaralama saxlanılır…',saved:'Qaralama saxlanıldı',failed:'Saxlanılmadı. Dəyişikliklər formada qalır.',conflict:'Kart dəyişib. Davam etməzdən əvvəl cari versiyanı açın.',restore:'Qaralama və şəkillər bərpa olunur…',retry:'Yenidən cəhd et',list:'Qaralamalarım'}}[language]||null;
    if(!copy)return;
    const native=window.KidsMapNativeDraftMedia?.mount(form),media=window.KidsMapDraftMedia?.mount(form,native);
    form.dataset.draftUrl=config.collectionUrl;
    const panel=document.createElement('div');panel.className='km-staff-save-panel';
    const status=document.createElement('span');status.dataset.kmStaffSaveStatus='';status.setAttribute('role','status');status.setAttribute('aria-live','polite');
    const retry=document.createElement('button');retry.type='button';retry.textContent=copy.retry;retry.hidden=true;
    const list=document.createElement('a');list.href=config.listUrl;list.textContent=copy.list;
    const current=document.createElement('a'),currentUrl=new URL(location.href);for(const key of ['draft_id','draft_session','draft_current'])currentUrl.searchParams.delete(key);current.href=currentUrl.href;current.target='_blank';current.rel='noopener';current.hidden=true;current.textContent=language==='ru'?'Открыть актуальную форму':language==='az'?'Cari formanı aç':'Open the current form';
    panel.append(status,retry,list,current);form.prepend(panel);
    let draftId=null,version=0,saving=null,timer,readinessTimer,epoch=0,halted=false,restoring=false,interacted=false,submitting=false,restoreFailed=false,pendingText=null,mediaResume=null,lastSaveError=null,readinessController=null;
    const csrf=()=>form.elements.namedItem('csrfmiddlewaretoken')?.value||'';
    function fields(){const result={},data=new FormData(form);for(const name of config.fields){const controls=[...form.elements].filter(x=>x.name===name&&x.type!=='file');if(!controls.length)continue;
      if(controls.every(x=>x.type==='checkbox'))result[name]=controls.length===1?controls[0].checked:controls.filter(x=>x.checked).map(x=>x.value);
      else if(controls[0].multiple)result[name]=data.getAll(name);
      else {const value=data.get(name);if(value!==null)result[name]=value;else if(controls[0].disabled&&controls[0].type!=='radio')result[name]=controls[0].value;}
    }Object.assign(result,native?.captureState?.()||{});result._editor_base_signature=config.baseSignature;result._draft_media_selection=(native?.snapshotMedia?.()||[]).map(({id,role,order})=>({id,role,order}));return result;}
    const fingerprint=()=>JSON.stringify(fields());let savedFingerprint=fingerprint();
    const pending=()=>fingerprint()!==savedFingerprint||!!media?.hasPending();
    function show(state){status.textContent=copy[state];panel.dataset.state=state;retry.hidden=!['failed'].includes(state);current.hidden=state!=='conflict';}
    show('initial');
    async function json(url,options){const response=await fetch(url,{credentials:'same-origin',...options});let result;try{result=await response.json();}catch{throw Object.assign(new Error('invalid_response'),{status:response.status,kind:'server'});}if(!response.ok)throw Object.assign(new Error(result.status||'request_failed'),{status:response.status});return result;}
    function adopt(result){draftId=result.draft_id;version=result.version;let hidden=form.elements.namedItem('server_draft_id');if(!hidden){hidden=document.createElement('input');hidden.type='hidden';hidden.name='server_draft_id';form.append(hidden);}hidden.value=draftId;let versionInput=form.elements.namedItem('server_draft_version');if(!versionInput){versionInput=document.createElement('input');versionInput.type='hidden';versionInput.name='server_draft_version';form.append(versionInput);}versionInput.value=String(version);const url=new URL(location.href);url.searchParams.set('draft_id',draftId);history.replaceState(history.state,'',url);}
    function apply(values){form.dispatchEvent(new CustomEvent('km:location-restore-start',{bubbles:true}));try{for(const [name,value]of Object.entries(values||{})){const controls=[...form.elements].filter(x=>x.name===name&&x.type!=='file');for(const input of controls){if(input.type==='checkbox')input.checked=Array.isArray(value)?value.includes(input.value):!!value;else if(input.type==='radio')input.checked=String(input.value)===String(value);else if(input.multiple){for(const option of input.options)option.selected=Array.isArray(value)&&value.includes(option.value);}else input.value=typeof value==='object'?JSON.stringify(value):String(value??'');}controls[0]?.dispatchEvent(new Event('input',{bubbles:true}));controls[0]?.dispatchEvent(new Event('change',{bubbles:true}));if(name==='structured_schedule')controls[0]?.dispatchEvent(new Event('km:schedule-import',{bubbles:true}));}}finally{form.dispatchEvent(new CustomEvent('km:location-restore-end',{bubbles:true}));}}
    async function restore(){const id=new URL(location.href).searchParams.get('draft_id');if(!id)return;restoring=true;form.inert=true;form.setAttribute('aria-busy','true');show('restore');try{
      const result=await json(config.collectionUrl+encodeURIComponent(id)+'/');
      if(result.target_type!=='place'||result.target_id!==config.targetId||result.schema_version!==config.schemaVersion||result.source_version!==config.sourceVersion||result.materialized_place_id||result.fields?._editor_base_signature!==config.baseSignature)throw Object.assign(new Error('stale_draft'),{status:409});
      apply(result.fields);await media?.restore(result);native?.restoreState?.(result.fields);adopt(result);savedFingerprint=fingerprint();halted=false;restoreFailed=false;if(media?.hasPending()){interacted=true;show('dirty');}else{show('saved');form.dispatchEvent(new Event('km:draft-saved'));}
    }catch(error){lastSaveError=error;halted=true;restoreFailed=true;show(error.status===409?'conflict':'failed');}finally{restoring=false;form.inert=false;form.removeAttribute('aria-busy');scheduleReadiness();if(media?.hasPending())schedule();}}
    async function save(){if(saving)return saving;if(halted||restoring||submitting)return false;clearTimeout(timer);
      if(!draftId)draftId=crypto.randomUUID();lastSaveError=null;saving=(async()=>{show('saving');try{
        if(mediaResume){mediaResume=await media.save(mediaResume,result=>{mediaResume=result;adopt(result);});adopt(mediaResume);mediaResume=null;}
        if(!pendingText)pendingText={draft_id:draftId,target_type:'place',target_id:config.targetId,schema_version:config.schemaVersion,source_version:config.sourceVersion,expected_version:version,fields:fields()};
        const signature=JSON.stringify(pendingText.fields);
        let result=await json(config.collectionUrl,{method:'POST',headers:{'Content-Type':'application/json','X-CSRFToken':csrf()},body:JSON.stringify(pendingText)});if(typeof result.draft_id!=='string'||!Number.isInteger(result.version)||result.version<1)throw Object.assign(new Error('invalid_response'),{kind:'server'});pendingText=null;
        adopt(result);mediaResume=media?result:null;result=await media?.save(result,next=>{mediaResume=next;adopt(next);})||result;mediaResume=null;adopt(result);savedFingerprint=signature;
        if(pending()){show('dirty');schedule();}else{show('saved');form.dispatchEvent(new Event('km:draft-saved'));}return !pending();
      }catch(error){lastSaveError=error;if(error.status===409)halted=true;if(error.status&&error.status<500)pendingText=null;show(error.status===409?'conflict':'failed');return false;}})();
      try{return await saving;}finally{saving=null;}
    }
    function schedule(){clearTimeout(timer);if(interacted&&!halted&&!restoring&&!submitting)timer=setTimeout(save,1200);}
    async function checkReadiness(){const button=form.querySelector('[data-km-preview]');if(!button?.formAction||restoring||submitting)return;const checkEpoch=++epoch,data=new FormData(form);for(const [name,value]of [...data])if(value instanceof File)data.delete(name);data.delete('gallery_order');data.set('_km_check_required','1');const values=Object.fromEntries([...data].filter(([,value])=>typeof value==='string'));readinessController?.abort();readinessController=new AbortController();try{const response=await fetch(button.formAction,{method:'POST',body:data,credentials:'same-origin',signal:readinessController.signal,headers:{'X-CSRFToken':csrf()}});if(!response.ok&&response.status!==422)return;const result=await response.json();if(checkEpoch!==epoch)return;if(result.readiness)form.dispatchEvent(new CustomEvent('km:readiness',{detail:result.readiness}));if(result.errors&&typeof result.errors==='object'&&!Array.isArray(result.errors))form.dispatchEvent(new CustomEvent('km:server-validation',{detail:{errors:result.errors,error_targets:result.error_targets||{},values}}));}catch{/* Keep pending state: a failed request cannot confirm readiness. */}}
    function scheduleReadiness(){++epoch;clearTimeout(readinessTimer);form.dispatchEvent(new CustomEvent('km:readiness',{detail:{pending:true}}));readinessTimer=setTimeout(checkReadiness,500);}
    form.addEventListener('km:validation-request',scheduleReadiness);
    function manualSave(){const operation=async()=>{if(restoreFailed)await restore();const ok=await save();return {ok,error:lastSaveError||(halted?{status:409}:{kind:'pending'})};};return window.KidsMapEditorFeedback?window.KidsMapEditorFeedback.run(form,'draft',operation):operation().then(result=>result.ok);}
    for(const type of ['pointerdown','keydown'])form.addEventListener(type,()=>{interacted=true;});
    for(const type of ['input','change','km:photos-change'])form.addEventListener(type,event=>{if(restoring||native?.isRestoring?.()||media?.isRestoring?.())return;if(event.isTrusted)interacted=true;scheduleReadiness();if(pending()){show('dirty');schedule();}});
    form.addEventListener('submit',event=>{if(halted||restoring||restoreFailed||submitting){event.preventDefault();event.stopImmediatePropagation();if(!submitting)window.KidsMapEditorFeedback?.report(form,{action:'save',outcome:halted?'conflict':'pending'});return;}if(event.submitter?.matches('[data-km-preview]'))return;const button=event.submitter,isDraft=button?.name==='_save_draft'||(button?.name==='action'&&button.value==='draft');if(isDraft&&!config.targetId&&(!form.elements.namedItem('name_az')?.value.trim()||!form.elements.namedItem('category')?.value)){event.preventDefault();event.stopImmediatePropagation();interacted=true;manualSave();return;}if(saving){event.preventDefault();event.stopImmediatePropagation();saving.then(ok=>{if(ok)form.requestSubmit(button);else if(window.KidsMapEditorFeedback)window.KidsMapEditorFeedback.report(form,{action:isDraft?'draft':'save',outcome:window.KidsMapEditorFeedback.classify(lastSaveError||{kind:'pending'})});});return;}if(!event.defaultPrevented){submitting=true;clearTimeout(timer);queueMicrotask(()=>{if(event.defaultPrevented)submitting=false;});}},true);
    window.addEventListener('online',()=>{if(pending()&&!halted)save();});
    retry.addEventListener('click',manualSave);
    form.kmDraftSave=manualSave;form.kmDraftHasPending=()=>pending()||!!saving;form.kmDraftReady=restore();setTimeout(()=>{if(!interacted&&!draftId&&!restoring){savedFingerprint=fingerprint();show('initial');}},0);
    scheduleReadiness();
  }
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',init);else init();
})();
