/* Private gallery transport. The caller serializes this with its text draft saves. */
(() => {
  'use strict';
  function mount(form, editor) {
    if (form.kidsmapDraftMedia) return form.kidsmapDraftMedia;
    if (!editor?.snapshotMedia) return null;
    let savedFingerprint = '[]', restoring = false, inFlight = null, failedOperation = null, missingUploads = false, recoveryNotice;
    const snapshot = () => editor.snapshotMedia();
    const key = rows => JSON.stringify(rows.map(x=>({id:x.id,role:x.role,order:x.order,size:x.file?.size})));
    const fingerprint = () => key(snapshot());
    const endpoint = draft => `${form.dataset.draftUrl || '/api/drafts/'}${draft.draft_id}/media/`;
    const csrf = () => form.elements.namedItem('csrfmiddlewaretoken').value;
    function showMissing(){
      const lang=(document.documentElement.lang||'az').split('-')[0],copy=({ru:['Часть фотографий не успела загрузиться до закрытия страницы. Уже загруженные фото восстановлены. Добавьте недостающие заново или сохраните только доступные.','Сохранить доступные фотографии'],az:['Səhifə bağlanmazdan əvvəl bəzi şəkillər yüklənmədi. Yüklənmiş şəkillər bərpa edilib. Çatışmayanları yenidən əlavə edin və ya yalnız mövcud şəkilləri saxlayın.','Mövcud şəkilləri saxla'],en:['Some photos did not finish uploading before the page closed. Uploaded photos have been restored. Add the missing photos again or keep only the available photos.','Keep available photos']})[lang]||['Some photos did not finish uploading. Add them again or keep the available photos.','Keep available photos'];
      recoveryNotice?.remove();recoveryNotice=document.createElement('div');recoveryNotice.className='km-editor-media-recovery';recoveryNotice.setAttribute('role','alert');const message=document.createElement('p');message.textContent=copy[0];const button=document.createElement('button');button.type='button';button.textContent=copy[1];button.addEventListener('click',()=>{missingUploads=false;recoveryNotice.remove();form.dispatchEvent(new Event('km:photos-change',{bubbles:true}));});recoveryNotice.append(message,button);form.prepend(recoveryNotice);
    }
    form.addEventListener('submit',event=>{if(missingUploads){event.preventDefault();event.stopImmediatePropagation();recoveryNotice?.scrollIntoView?.({block:'center'});}},true);
    async function request(url, method, body) {
      const headers={'X-CSRFToken':csrf()};
      if (!(body instanceof FormData)) {headers['Content-Type']='application/json';body=JSON.stringify(body);}
      const operation={url,method,body,headers};
      try {
        const response=await fetch(url,{method,body,headers,credentials:'same-origin'});
        const result=await response.json();
        if(!response.ok)throw Object.assign(new Error(result.status || 'media_save_failed'),{status:response.status,conflict:response.status===409,result});
        failedOperation=null;return result;
      }catch(error){if(!error.status||error.status>=500)failedOperation=operation;else failedOperation=null;throw error;}
    }
    async function save(draft, onVersion=()=>{}) {
      if(inFlight)return inFlight;
      inFlight=(async()=>{
        await editor.ready?.();
        if(missingUploads)throw new Error('missing_uploads_need_confirmation');
        if(editor.blocking?.())throw new Error('media_not_ready');
        const rows=snapshot(),signature=key(rows),ids=rows.map(x=>x.id);
        let current=draft;
        // Retry the identical UUID/version request before any newer text/media write.
        if(failedOperation){const old=failedOperation;let body=old.body;if(old.headers['Content-Type']==='application/json')body=JSON.parse(body);current=await request(old.url,old.method,body);onVersion(current);}
        const selected=(current.media_manifest||[]).filter(x=>x.role!=='pending');
        const matches=!(current.media_manifest||[]).some(x=>x.role==='pending')&&selected.length===rows.length&&rows.every(x=>selected.some(y=>y.id===x.id&&y.role===x.role&&y.order===x.order));
        if(matches){savedFingerprint=signature;editor.markDraftMedia?.(ids,'saved');return current;}
        editor.markDraftMedia?.(ids,'saving');
        try {
          for(const row of rows){
            if((current.media_manifest||[]).some(item=>item.id===row.id))continue;
            const data=new FormData();data.set('expected_version',String(current.version));data.set('media_id',row.id);data.set('photo',row.file,row.file.name);data.set('desired_role',row.role);data.set('desired_order',String(row.order));
            current=await request(endpoint(current),'POST',data);onVersion(current);
          }
          current=await request(endpoint(current),'PUT',{expected_version:current.version,items:rows.map(({id,role,order})=>({id,role,order}))});
          onVersion(current);savedFingerprint=signature;editor.markDraftMedia?.(ids,'saved');return current;
        } catch(error){editor.markDraftMedia?.(ids,'save-error');throw error;}
      })();
      try{return await inFlight;}finally{inFlight=null;}
    }
    async function restore(detail) {
      restoring=true;
      try {
        await editor.ready?.();
        let manifest=detail.media_manifest||[];
        const pending=manifest.some(item=>item.role==='pending');
        const intent=detail.fields?._draft_media_selection;
        missingUploads=false;
        if(Array.isArray(intent)){
          missingUploads=intent.some(item=>!manifest.some(saved=>saved.id===item.id));
          manifest=intent.flatMap(item=>{const saved=manifest.find(row=>row.id===item.id);return saved?[{...saved,role:item.role,order:item.order}]:[];});
        }else{
          if(pending&&manifest.some(item=>item.role==='pending'&&!['main','cover','gallery'].includes(item.desired_role)))throw new Error('unfinished_media_requires_retry');
          const replacements=new Set(manifest.filter(x=>x.role==='pending'&&x.desired_role!=='gallery').map(x=>x.desired_role));
          manifest=manifest.filter(x=>x.role==='pending'||!replacements.has(x.role)).map(item=>item.role==='pending'?{...item,role:item.desired_role,order:item.desired_order}:item);
        }
        let galleryIndex=0;manifest.sort((a,b)=>a.order-b.order);manifest=manifest.map(item=>item.role==='gallery'?{...item,order:galleryIndex++}:item);
        // Legacy one-photo drafts are still private and must remain recoverable.
        const legacy=!Array.isArray(intent)&&!manifest.length&&detail.photo_saved;
        if(legacy)manifest=[{id:crypto.randomUUID(),role:'main',order:0,url:`${form.dataset.draftUrl||'/api/drafts/'}${detail.draft_id}/photo/`,name:'draft.webp'}];
        await editor.restoreMedia(manifest,async item=>{
          const url=new URL(item.url,location.href);if(url.origin!==location.origin)throw new Error('foreign_media_url');
          const response=await fetch(url.href,{credentials:'same-origin'});if(!response.ok)throw new Error('media_restore_failed');
          const blob=await response.blob();return new File([blob],item.name||'photo.webp',{type:blob.type||'image/webp'});
        });
        savedFingerprint=pending||legacy||missingUploads?'__uncommitted__':fingerprint();
        if(missingUploads)showMissing();
      }finally{restoring=false;}
    }
    const api={save,restore,fingerprint,blocking:()=>missingUploads,hasPending:()=>missingUploads||!!editor.blocking?.()||fingerprint()!==savedFingerprint,isRestoring:()=>restoring};
    form.kidsmapDraftMedia=api;return api;
  }
  window.KidsMapDraftMedia={mount};
})();
