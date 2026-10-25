/* Adapt staff file inputs to the same private-draft gallery transport. */
(() => {
  'use strict';
  const lang=(document.documentElement.lang||'az').split('-')[0];
  const copy=({ru:{main:'Сделать главным',remove:'Удалить',up:'Выше',down:'Ниже',saved:'Сохранено в черновике',saving:'Сохраняем фото…',error:'Фото не сохранено. Повторите сохранение.',ready:'Фото выбрано, ожидает сохранения'},az:{main:'Əsas şəkil et',remove:'Sil',up:'Yuxarı',down:'Aşağı',saved:'Qaralamada saxlanıldı',saving:'Şəkil saxlanılır…',error:'Şəkil saxlanılmadı. Yenidən cəhd edin.',ready:'Şəkil seçilib, saxlanması gözlənilir'},en:{main:'Make main',remove:'Remove',up:'Earlier',down:'Later',saved:'Saved in draft',saving:'Saving photo…',error:'Photo not saved. Try saving again.',ready:'Selected, waiting to save'}})[lang]||{main:'Make main',remove:'Remove',up:'Earlier',down:'Later',saved:'Saved',saving:'Saving…',error:'Retry saving',ready:'Waiting to save'};
  function mount(form){
    if(form.kmNativeMedia)return form.kmNativeMedia;
    const ids=new WeakMap(),states=new Map(),urls=[];let restoring=false,settingFiles=false,mainTask=null;
    const field=name=>form.elements.namedItem(name);
    const gallery=field('gallery_images');const adminRoot=form.querySelector('[data-gallery-root]');
    const uuid=file=>{if(!ids.has(file))ids.set(file,crypto.randomUUID());return ids.get(file);};
    const setFiles=(input,files)=>{if(!input)return;const d=new DataTransfer();files.forEach(f=>d.items.add(f));input.files=d.files;settingFiles=true;try{input.dispatchEvent(new Event('change',{bubbles:true}));}finally{settingFiles=false;}};
    const cards=()=>[...form.querySelectorAll('[data-gallery-card]')];
    const active=card=>!card.hidden&&!card.querySelector('[name$="-DELETE"]')?.checked;
    const galleryFiles=()=>gallery?[...gallery.files]:cards().filter(active).flatMap(card=>[...(card.querySelector('input[type=file]')?.files||[])]);
    const cardKey=card=>card.dataset.galleryKey||(card.querySelector('[name$="-id"]')?.value?'saved:'+card.querySelector('[name$="-id"]').value:'');
    const deleteKey=key=>key.startsWith('saved:')?key.slice(6):key;
    let savedRows=[];
    try{savedRows=JSON.parse(document.getElementById('km-volunteer-gallery')?.textContent||'[]');}catch{}
    if(!Array.isArray(savedRows))savedRows=[];
    savedRows=savedRows.filter(row=>row&&/^(saved:[1-9]\d*|candidate:[a-f0-9]{64})$/.test(row.key)&&typeof row.url==='string');
    let entries=savedRows.map(row=>({...row}));
    const deletionBoxes=()=>[...form.querySelectorAll('[name=delete_gallery_ids]')].filter(x=>x.type==='checkbox');
    const visibleEntries=()=>entries.filter(row=>row.file||!deletionBoxes().some(x=>x.value===deleteKey(row.key)&&x.checked));
    function syncGallery(emit=true){
      if(!gallery)return;
      const current=visibleEntries(),files=current.filter(row=>row.file).map(row=>row.file);
      const d=new DataTransfer();files.forEach(file=>d.items.add(file));gallery.files=d.files;
      let index=0;const order=current.map(row=>row.file?'new:'+index++:row.key);
      if(field('gallery_order'))field('gallery_order').value=JSON.stringify(order);
      render();if(emit)form.dispatchEvent(new Event('km:photos-change',{bubbles:true}));
    }
    async function materialize(row){
      if(row.file)return new File([row.file],row.file.name,{type:row.file.type,lastModified:row.file.lastModified});
      const url=new URL(row.url,location.href);
      if(url.origin!==location.origin||!['http:','https:'].includes(url.protocol))throw new Error('foreign_media_url');
      const response=await fetch(url.href,{credentials:'same-origin'});
      if(!response.ok)throw new Error('media_download_failed');
      const blob=await response.blob();let type=blob.type;
      if(!type||type==='application/octet-stream'){
        type=({webp:'image/webp',png:'image/png',jpg:'image/jpeg',jpeg:'image/jpeg'})[url.pathname.split('.').pop().toLowerCase()];
        if(!type||typeof createImageBitmap!=='function')throw new Error('invalid_media');
        const decoded=await createImageBitmap(blob);decoded.close();
      }
      if(!type.startsWith('image/'))throw new Error('invalid_media');
      return new File([blob],url.pathname.split('/').pop()||'photo.webp',{type});
    }
    function chooseMain(row,host){
      if(mainTask)return;
      mainTask=(async()=>{
        // Resolve both images before changing any input: failed downloads keep
        // the current cover/gallery intact. Admin swaps just like the owner UI.
        const file=await materialize(row);
        let previous=null;
        if(adminRoot){
          const current=field('photo')?.files?.[0],url=form.querySelector('[data-main-photo-preview]')?.dataset.mainPhotoInitialUrl;
          if(!field('photo-clear')?.checked&&(current||url))previous=await materialize({file:current,url});
        }
        if(field('photo-clear'))field('photo-clear').checked=false;
        setFiles(field('photo'),[file]);
        if(adminRoot){
          setFiles(host.querySelector('input[type=file]'),previous?[previous]:[]);
          const remove=host.querySelector('[name$="-DELETE"]');if(remove)remove.checked=!previous;
          host.hidden=!previous;host.classList.toggle('is-hidden',!previous);
          host.querySelector('[name$="-order"]')?.dispatchEvent(new Event('change',{bubbles:true}));
        }
        host.querySelector('[data-media-error]')?.remove();
      })().catch(()=>{let error=host.querySelector('[data-media-error]');if(!error){error=document.createElement('small');error.dataset.mediaError='';error.setAttribute('role','alert');host.append(error);}error.textContent=copy.error;}).finally(()=>{mainTask=null;form.dispatchEvent(new Event('km:photos-change',{bubbles:true}));});
    }
    function snapshotMedia(){
      const rows=[];for(const [name,role]of[['photo','main'],['cover_photo','cover']]){const input=field(name);if(input?.files?.[0]&&!field(name+'-clear')?.checked)rows.push({id:uuid(input.files[0]),role,order:0,file:input.files[0]});}
      galleryFiles().forEach((file,order)=>rows.push({id:uuid(file),role:'gallery',order,file}));return rows;
    }
    let grid;
    if(gallery){grid=document.createElement('div');grid.className='km-native-gallery';grid.dataset.kmNativeGallery='';gallery.parentElement.append(grid);const original=form.querySelector('[data-editor-gallery-list]');if(original)original.hidden=true;}
    function render(){
      if(!grid)return;urls.splice(0).forEach(url=>URL.revokeObjectURL(url));grid.replaceChildren();
      const current=visibleEntries();current.forEach((entry,index)=>{
        const file=entry.file,row=document.createElement('article'),image=document.createElement('img'),name=document.createElement('strong');image.alt=file?.name||'';image.src=file?URL.createObjectURL(file):entry.url;if(file)urls.push(image.src);name.textContent=file?.name||`${index+1}`;row.append(image,name);
        if(file){const state=document.createElement('small');state.dataset.draftMediaState='';state.dataset.state=states.get(uuid(file))||'ready';state.textContent=copy[state.dataset.state==='save-error'?'error':state.dataset.state]||copy.ready;row.append(state);}
        const actions=document.createElement('div');actions.className='km-native-gallery-actions';
        function button(label,handler,disabled=false,move){const b=document.createElement('button');b.type='button';b.textContent=label;b.disabled=disabled;if(move!==undefined)b.dataset.mediaMove=move;b.addEventListener('click',handler);actions.append(b);return b;}
        button(copy.main,()=>chooseMain(entry,row)).dataset.mediaMain='';
        for(const delta of [-1,1])button(delta<0?'↑ '+copy.up:'↓ '+copy.down,()=>{const next=[...current];[next[index],next[index+delta]]=[next[index+delta],next[index]];entries=[...next,...entries.filter(x=>!current.includes(x))];syncGallery();grid.querySelectorAll('article')[index+delta]?.querySelector(`[data-media-move="${delta}"]`)?.focus({preventScroll:true});},index+delta<0||index+delta>=current.length,delta);
        button(copy.remove,()=>{if(file)entries=entries.filter(x=>x!==entry);else{const checkbox=deletionBoxes().find(x=>x.value===deleteKey(entry.key));if(checkbox)checkbox.checked=true;}syncGallery();}).dataset.mediaRemove='';row.append(actions);grid.append(row);
      });
    }
    if(gallery){gallery.addEventListener('change',()=>{
      const selected=[...gallery.files];
      if(settingFiles||restoring)entries=[...entries.filter(x=>!x.file),...selected.map(file=>({file}))];
      else for(const file of selected)if(!entries.some(x=>x.file===file))entries.push({file});
      syncGallery();
    });deletionBoxes().forEach(input=>input.addEventListener('change',()=>syncGallery()));}
    if(adminRoot){
      const enhance=()=>cards().forEach(card=>{
        if(!card.querySelector('[data-media-actions]')){
          const actions=document.createElement('div');actions.dataset.mediaActions='';
          const button=(label,action)=>{const node=document.createElement('button');node.type='button';node.className='km-pf-btn km-pf-btn--ghost km-pf-btn--sm';node.textContent=label;node.addEventListener('click',action);actions.append(node);return node;};
          button(copy.main,()=>{const file=card.querySelector('input[type=file]')?.files?.[0],url=card.querySelector('[data-gallery-preview]')?.dataset.galleryInitialUrl;if(file||url)chooseMain({file,url},card);}).dataset.mediaMain='';
          const replace=({ru:'Заменить',az:'Dəyişdir',en:'Replace'})[lang]||'Replace';
          button(replace,()=>card.querySelector('input[type=file]')?.click()).dataset.mediaReplace='';
          for(const delta of [-1,1]){
            const node=button(delta<0?'↑ '+copy.up:'↓ '+copy.down,()=>{
              const current=cards().filter(active),index=current.indexOf(card),other=current[index+delta];if(!other)return;
              if(delta<0)other.before(card);else other.after(card);
              card.querySelector('[name$="-order"]')?.dispatchEvent(new Event('change',{bubbles:true}));
              form.dispatchEvent(new Event('km:photos-change',{bubbles:true}));node.focus({preventScroll:true});
            });node.dataset.mediaMove=String(delta);
          }
          card.append(actions);
        }
        const current=cards().filter(active),index=current.indexOf(card);
        for(const node of card.querySelectorAll('[data-media-move]'))node.disabled=index<0||index+Number(node.dataset.mediaMove)<0||index+Number(node.dataset.mediaMove)>=current.length;
      });
      enhance();new MutationObserver(enhance).observe(adminRoot,{childList:true,subtree:true});
    }
    function captureState(){
      const state={'photo-clear':!!field('photo-clear')?.checked,'cover_photo-clear':!!field('cover_photo-clear')?.checked};
      if(adminRoot){let newIndex=0;state.delete_gallery_ids=[];state.gallery_order=[];state.gallery_captions={};
        cards().forEach(card=>{const key=cardKey(card),file=card.querySelector('input[type=file]')?.files?.[0];
          if(!active(card)){if(key)state.delete_gallery_ids.push(deleteKey(key));return;}
          const token=file?`new:${newIndex++}`:key;
          if(file&&key)state.delete_gallery_ids.push(deleteKey(key));
          if(token){state.gallery_order.push(token);state.gallery_captions[token]=card.querySelector('[name$="-caption"]')?.value||'';}
        });
      }else{state.delete_gallery_ids=[...form.querySelectorAll('[name=delete_gallery_ids]:checked')].map(x=>x.value);try{state.gallery_order=JSON.parse(field('gallery_order')?.value||'[]');}catch{state.gallery_order=[];}}
      // Deletions are a set. DOM order can change after sorting/reopening and
      // must not make an unchanged private working copy look dirty again.
      if(state.delete_gallery_ids)state.delete_gallery_ids.sort();
      return state;
    }
    async function restoreMedia(manifest,download){
      restoring=true;try{
        const rows=await Promise.all(manifest.filter(x=>['main','cover','gallery'].includes(x.role)).map(async x=>{const file=await download(x);ids.set(file,x.id);states.set(x.id,'saved');return {...x,file};}));
        for(const [name,role]of[['photo','main'],['cover_photo','cover']]){const row=rows.find(x=>x.role===role);if(row)setFiles(field(name),[row.file]);}
        const files=rows.filter(x=>x.role==='gallery').sort((a,b)=>a.order-b.order).map(x=>x.file);
        if(gallery)setFiles(gallery,files);else if(adminRoot?.kidsmapAddGalleryPhotos)adminRoot.kidsmapAddGalleryPhotos(files);
        render();
      }finally{restoring=false;}
    }
    function restoreState(state){
      for(const name of ['photo-clear','cover_photo-clear'])if(field(name)){field(name).checked=!!state[name];field(name).dispatchEvent(new Event('change',{bubbles:true}));}
      if(!adminRoot){
        if(gallery){const byToken=new Map();let index=0;entries.forEach(row=>byToken.set(row.file?'new:'+index++:row.key,row));const order=state.gallery_order||[],ordered=order.map(key=>byToken.get(key)).filter(Boolean);entries=[...ordered,...entries.filter(row=>!ordered.includes(row))];const deleted=new Set(state.delete_gallery_ids||[]);deletionBoxes().forEach(input=>input.checked=deleted.has(input.value));syncGallery(false);}return;
      }
      const deleted=new Set(state.delete_gallery_ids||[]),newCards=[];const byToken=new Map();
      cards().forEach(card=>{const key=cardKey(card),del=card.querySelector('[name$="-DELETE"]');if(key&&deleted.has(deleteKey(key))){if(del)del.checked=true;card.hidden=true;}else{if(del)del.checked=false;card.hidden=false;if(card.querySelector('input[type=file]')?.files?.length)newCards.push(card);else if(key)byToken.set(key,card);}});
      newCards.forEach((card,i)=>byToken.set('new:'+i,card));const order=state.gallery_order||[];
      order.forEach((token,i)=>{const card=byToken.get(token);if(card){card.parentElement.append(card);const input=card.querySelector('[name$="-order"]');if(input)input.value=i+1;}});
      for(const [token,caption]of Object.entries(state.gallery_captions||{})){const input=byToken.get(token)?.querySelector('[name$="-caption"]');if(input&&typeof caption==='string'){input.value=caption;input.dispatchEvent(new Event('input',{bubbles:true}));}}
    }
    function markDraftMedia(mediaIds,state){mediaIds.forEach(id=>states.set(id,state));render();
      snapshotMedia().filter(x=>mediaIds.includes(x.id)).forEach(x=>{const input=[...form.querySelectorAll('input[type=file]')].find(i=>[...i.files].includes(x.file));const host=input?.closest('[data-gallery-card],[data-pf-field],[data-main-photo-root],.kv-photo-card')||input?.parentElement;if(!host||host===grid)return;let status=host.querySelector(':scope > [data-draft-media-state]');if(!status){status=document.createElement('small');status.dataset.draftMediaState='';host.append(status);}status.dataset.state=state;status.textContent=copy[state==='save-error'?'error':state]||copy.ready;});
    }
    form.kmNativeMedia={snapshotMedia,restoreMedia,markDraftMedia,captureState,restoreState,ready:async()=>{if(mainTask)await mainTask;},blocking:()=>!!mainTask,isRestoring:()=>restoring};if(gallery)syncGallery(false);else render();return form.kmNativeMedia;
  }
  window.KidsMapNativeDraftMedia={mount};
})();
