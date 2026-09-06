(() => {
  'use strict';
  const translations = {
    ru: {choose:'Выбрать фото', drop:'Перетащите сюда или нажмите для выбора', ready:'Готово к сохранению', saved:'Сохранено', preparing:'Загружается и обрабатывается', queued:'В очереди', saving:'Загружается', error:'Ошибка — повторить', retry:'Повторить', remove:'Удалить', main:'Сделать главным', up:'Раньше', down:'Позже', count:'из', duplicate:'Это фото уже добавлено', format:'Поддерживаются JPG, PNG, WEBP, HEIC/HEIF', size:'Файл пустой или превышает 15 МБ', pixels:'Максимум 50 Мп и 12000 пикселей по стороне', full:'Можно добавить до 10 дополнительных фото', one:'Для главного фото выберите один файл', failed:'Не удалось обработать фото. Повторите попытку.', wait:'Дождитесь обработки фото или удалите файлы с ошибками.', unsaved:'Изменения фотографий ещё не сохранены', saveFailed:'Не удалось сохранить. Фото остаются в форме — повторите сохранение.', order:'Порядок можно изменить стрелками или перетаскиванием.', heif:'HEIC сейчас недоступен. Выберите JPG, PNG или WEBP.', batch:'Общий размер подготовленных фото превышает 22 МБ.'},
    az: {choose:'Şəkil seçin', drop:'Buraya sürükləyin və ya seçmək üçün basın', ready:'Saxlamağa hazırdır', saved:'Saxlanıldı', preparing:'Yüklənir və hazırlanır', queued:'Növbədədir', saving:'Yüklənir', error:'Xəta — təkrarlayın', retry:'Təkrarla', remove:'Sil', main:'Əsas şəkil et', up:'Əvvələ', down:'Sonraya', count:'/', duplicate:'Bu şəkil artıq əlavə edilib', format:'JPG, PNG, WEBP, HEIC/HEIF dəstəklənir', size:'Fayl boşdur və ya 15 MB-dan böyükdür', pixels:'Maksimum 50 MP və hər tərəf 12000 piksel', full:'10-dək əlavə şəkil seçilə bilər', one:'Əsas şəkil üçün bir fayl seçin', failed:'Şəkil hazırlanmadı. Yenidən cəhd edin.', wait:'Hazırlanmanı gözləyin və ya xətalı şəkilləri silin.', unsaved:'Şəkil dəyişiklikləri hələ saxlanılmayıb', saveFailed:'Saxlanılmadı. Şəkillər formadadır — yenidən saxlayın.', order:'Sıranı oxlarla və ya sürükləyərək dəyişin.', heif:'HEIC hazırda əlçatan deyil. JPG, PNG və ya WEBP seçin.', batch:'Hazır şəkillərin ümumi ölçüsü 22 MB-dan böyükdür.'},
    en: {choose:'Choose photos', drop:'Drop here or click to choose', ready:'Ready to save', saved:'Saved', preparing:'Uploading and processing', queued:'Queued', saving:'Uploading', error:'Error — retry', retry:'Retry', remove:'Remove', main:'Make main photo', up:'Earlier', down:'Later', count:'of', duplicate:'This photo is already added', format:'Supported: JPG, PNG, WEBP, HEIC/HEIF', size:'File is empty or exceeds 15 MB', pixels:'Maximum 50 MP and 12000 pixels per side', full:'You can add up to 10 gallery photos', one:'Choose one main photo', failed:'Could not process photo. Please retry.', wait:'Wait for processing or remove photos with errors.', unsaved:'Photo changes are not saved yet', saveFailed:'Could not save. Photos remain in this form — retry saving.', order:'Change the order with arrows or drag and drop.', heif:'HEIC is unavailable. Choose JPG, PNG or WEBP.', batch:'Prepared photos exceed 22 MB in total.'},
  };
  const extensions = {jpg:'jpeg', jpeg:'jpeg', png:'png', webp:'webp', heic:'heif', heif:'heif', hif:'heif'};
  const mimeFormats = {'image/jpeg':'jpeg','image/jpg':'jpeg','image/png':'png','image/webp':'webp','image/heic':'heif','image/heif':'heif'};
  function signature(bytes) {
    if (bytes[0] === 255 && bytes[1] === 216 && bytes[2] === 255) return 'jpeg';
    if ([137,80,78,71,13,10,26,10].every((byte, index) => bytes[index] === byte)) return 'png';
    const text = (from, length) => String.fromCharCode(...bytes.slice(from, from + length));
    if (text(0,4) === 'RIFF' && text(8,4) === 'WEBP') return 'webp';
    if (text(4,4) === 'ftyp' && /heic|heix|heim|heis|hevc|hevx|hevm|hevs|mif1|msf1/.test(text(8,32))) return 'heif';
    return '';
  }
  function dimensions(bytes, format) {
    const view = new DataView(bytes.buffer, bytes.byteOffset, bytes.byteLength);
    if (format === 'png' && bytes.length >= 24) return [view.getUint32(16), view.getUint32(20)];
    if (format === 'jpeg') {
      let offset = 2;
      while (offset + 9 < bytes.length && bytes[offset] === 255) {
        const marker = bytes[offset + 1], length = view.getUint16(offset + 2);
        if ([192,193,194,195,197,198,199,201,202,203,205,206,207].includes(marker)) return [view.getUint16(offset + 7), view.getUint16(offset + 5)];
        if (length < 2) break;
        offset += 2 + length;
      }
    }
    if (format === 'webp' && bytes.length >= 30 && String.fromCharCode(...bytes.slice(12,16)) === 'VP8X') {
      return [1 + bytes[24] + (bytes[25] << 8) + (bytes[26] << 16), 1 + bytes[27] + (bytes[28] << 8) + (bytes[29] << 16)];
    }
    return null; // Other headers, including HEIF, are checked by the server before decoding.
  }
  async function digest(buffer) {
    if (globalThis.crypto?.subtle) {
      return [...new Uint8Array(await crypto.subtle.digest('SHA-256', buffer))].map(byte => byte.toString(16).padStart(2,'0')).join('');
    }
    let a = 2166136261, b = 5381;
    for (const byte of new Uint8Array(buffer)) { a = Math.imul(a ^ byte, 16777619); b = Math.imul(b, 33) ^ byte; }
    return `${buffer.byteLength}:${a}:${b}`;
  }
  function mount(form) {
    const root = form.querySelector('[data-photo-editor]');
    if (!root || !globalThis.DataTransfer) return null;
    const rules = JSON.parse(document.getElementById('pw-photo-config').textContent);
    const copy = translations[(document.documentElement.lang || 'az').split('-')[0]] || translations.az;
    const input = name => form.elements.namedItem(name);
    const targets = {main: root.querySelector('[data-photo-items=main]'), gallery: root.querySelector('[data-photo-items=gallery]')};
    const status = root.querySelector('[data-photo-save-status]');
    const deletedInputs = [...root.querySelectorAll('input[name=delete_gallery_ids]')];
    const originalIds = deletedInputs.map(node => node.value);
    const readSaved = node => ({id: crypto.randomUUID(), name:node.dataset.photoName.split('/').pop(), url:node.dataset.photoUrl, preview:node.dataset.photoPreview, savedId:node.dataset.photoSaved, state:'saved'});
    let main = targets.main.querySelector('[data-photo-saved]') ? readSaved(targets.main.querySelector('[data-photo-saved]')) : null;
    let gallery = [...targets.gallery.querySelectorAll('[data-photo-saved]')].map(readSaved).filter(item => !deletedInputs.some(node => node.value === item.savedId && node.checked));
    const hadMain = !!main;
    let queue = Promise.resolve(), busy = 0, saving = false, requestId = null, changedPhotos = false;
    const items = () => [main, ...gallery].filter(Boolean);
    const present = item => items().includes(item);
    const blocking = () => busy > 0 || items().some(item => ['queued','preparing','error'].includes(item.state));
    const newFiles = () => gallery.filter(item => item.file);
    function fileList(files) { const transfer = new DataTransfer(); files.forEach(file => transfer.items.add(file)); return transfer.files; }
    function sync(notify = true) {
      input('photo').files = fileList(main?.file ? [main.file] : []);
      input('gallery_images').files = fileList(newFiles().map(item => item.file));
      input('photo-clear').checked = hadMain && !main;
      deletedInputs.forEach(node => { node.checked = !gallery.some(item => item.savedId === node.value); });
      input('gallery_order').value = JSON.stringify(gallery.filter(item => item.savedId || item.file).map(item => item.savedId ? `saved:${item.savedId}` : `new:${newFiles().indexOf(item)}`));
      root.querySelector('[data-photo-count]').textContent = `${gallery.length} ${copy.count} ${rules.maxGallery}`;
      if (notify) {
        delete status.dataset.savedError;
        requestId = null; changedPhotos = true;
        form.dispatchEvent(new Event('km:photos-change', {bubbles:true}));
      }
    }
    function release(item) { if (item?.objectUrl) URL.revokeObjectURL(item.objectUrl); }
    function message(target, name, text) {
      const row = document.createElement('p'); row.className = 'pw-photo-error'; row.textContent = `${name}: ${text}`;
      const dismiss = document.createElement('button'); dismiss.type = 'button'; dismiss.textContent = '×'; dismiss.setAttribute('aria-label', copy.remove + ': ' + name); dismiss.addEventListener('click', () => row.remove()); row.append(dismiss);
      const region = root.querySelector(`[data-photo-errors=${target}]`); region.append(row);
      while (region.children.length > 12) region.firstElementChild.remove();
    }
    function render() {
      for (const [target, list] of [['main',main ? [main] : []], ['gallery',gallery]]) {
        const active = document.activeElement?.dataset.photoAction, activeId = document.activeElement?.closest('[data-photo-id]')?.dataset.photoId;
        targets[target].replaceChildren();
        list.forEach((item, index) => {
          const row = document.createElement('article'); row.className = 'pw-photo-item'; row.dataset.photoId = item.id; row.dataset.state = item.state;
          row.draggable = target === 'gallery' && !saving && !busy;
          row.addEventListener('dragstart', event => { event.dataTransfer.setData('application/x-kidsmap-photo', item.id); event.dataTransfer.effectAllowed = 'move'; });
          row.addEventListener('dragover', event => { if (event.dataTransfer.types.includes('application/x-kidsmap-photo')) event.preventDefault(); });
          row.addEventListener('drop', event => {
            const id = event.dataTransfer.getData('application/x-kidsmap-photo');
            if (!id) return;
            event.preventDefault(); event.stopPropagation();
            const from = gallery.findIndex(entry => entry.id === id);
            if (from >= 0 && !saving && !busy) { const moved = gallery.splice(from,1)[0]; gallery.splice(index,0,moved); sync(); render(); }
          });
          if (item.preview) { const image = document.createElement('img'); image.src = item.preview; image.alt = item.name; image.width = 160; image.height = 120; image.loading = 'lazy'; image.decoding = 'async'; row.append(image); }
          const info = document.createElement('div'); info.className = 'pw-photo-item-info';
          const name = document.createElement('strong'); name.textContent = item.name; info.append(name);
          const state = document.createElement('p'); state.className = 'pw-photo-item-status'; state.setAttribute('aria-live','polite');
          state.textContent = item.error || (copy[item.state] || copy.ready) + (item.progress != null ? ` ${item.progress}%` : ''); info.append(state);
          const actions = document.createElement('div'); actions.className = 'pw-photo-item-actions';
          function button(action, title, handler, disabled = false) {
            const node = document.createElement('button'); node.type = 'button'; node.textContent = title; node.dataset.photoAction = action; node.setAttribute('aria-label', `${title}: ${item.name}`); node.disabled = saving || busy > 0 || disabled; node.addEventListener('click', handler); actions.append(node);
          }
          if (item.state === 'error') button('retry',copy.retry,() => { item.error = ''; item.state = 'queued'; enqueue(item,target); render(); });
          if (target === 'gallery') {
            button('main',copy.main,() => promote(item), !['ready','saved','save-error'].includes(item.state));
            button('up','↑ ' + copy.up,() => move(item,-1), index === 0);
            button('down','↓ ' + copy.down,() => move(item,1), index === gallery.length - 1);
          }
          button('remove',copy.remove,() => { if (target === 'main') main = item.previous || null; else gallery = gallery.filter(entry => entry !== item); release(item); sync(); render(); });
          info.append(actions); row.append(info); targets[target].append(row);
        });
        if (activeId && active) targets[target].querySelector(`[data-photo-id="${activeId}"] [data-photo-action="${active}"]`)?.focus({preventScroll:true});
      }
      if (!saving && changedPhotos && !status.dataset.savedError) status.textContent = copy.unsaved;
    }
    function move(item, direction) {
      const index = gallery.indexOf(item), next = index + direction;
      if (next < 0 || next >= gallery.length) return;
      [gallery[index], gallery[next]] = [gallery[next], gallery[index]]; sync(); render();
    }
    function send(url, data, responseType, progress) {
      return new Promise((resolve,reject) => {
        const xhr = new XMLHttpRequest(); xhr.open('POST',url); xhr.responseType = responseType; xhr.timeout = 120000;
        xhr.setRequestHeader('X-CSRFToken', input('csrfmiddlewaretoken').value);
        xhr.upload.onprogress = event => { if (event.lengthComputable) progress(Math.round(event.loaded / event.total * 100)); };
        xhr.onload = async () => {
          if (xhr.status >= 200 && xhr.status < 300) { resolve(xhr.response); return; }
          try {
            const body = JSON.parse(responseType === 'blob' ? await xhr.response.text() : xhr.responseText);
            reject(Object.assign(new Error(body.error || copy.saveFailed), {errors:body.errors}));
          } catch (error) { reject(new Error(copy.failed)); }
        };
        xhr.onerror = xhr.ontimeout = () => reject(new Error(copy.failed));
        xhr.send(data);
      });
    }
    async function preview(file) {
      let bitmap, temporaryUrl;
      if (globalThis.createImageBitmap) bitmap = await createImageBitmap(file);
      else {
        temporaryUrl = URL.createObjectURL(file);
        try {
          bitmap = await new Promise((resolve,reject) => {
            const image = new Image(); image.onload = () => resolve(image); image.onerror = () => reject(new Error(copy.failed)); image.src = temporaryUrl;
          });
        } catch (error) { URL.revokeObjectURL(temporaryUrl); throw error; }
      }
      const canvas = document.createElement('canvas'), ratio = Math.min(1,320 / Math.max(bitmap.width,bitmap.height));
      canvas.width = Math.max(1,Math.round(bitmap.width * ratio)); canvas.height = Math.max(1,Math.round(bitmap.height * ratio));
      try {
        canvas.getContext('2d').drawImage(bitmap,0,0,canvas.width,canvas.height);
        const blob = await new Promise(resolve => canvas.toBlob(resolve,'image/webp',0.76));
        if (!blob) throw new Error(copy.failed);
        return URL.createObjectURL(blob);
      } finally { bitmap.close?.(); if (temporaryUrl) URL.revokeObjectURL(temporaryUrl); canvas.width = canvas.height = 1; }
    }
    async function prepare(item, target) {
      if (!present(item)) return;
      item.state = 'preparing'; item.progress = 0; render();
      try {
        const buffer = await item.source.arrayBuffer(), bytes = new Uint8Array(buffer), format = signature(bytes);
        if (!format || extensions[item.name.split('.').pop().toLowerCase()] !== format || (mimeFormats[item.source.type] && mimeFormats[item.source.type] !== format)) throw new Error(copy.format);
        const size = dimensions(bytes,format);
        if (size && (!size[0] || !size[1] || size[0] * size[1] > rules.maxPixels || Math.max(...size) > rules.maxDimension)) throw new Error(copy.pixels);
        item.hash = await digest(buffer);
        if (items().some(other => other !== item && (other.hash === item.hash || other.optimizedHash === item.hash))) {
          message(target,item.name,copy.duplicate); if (main === item) main = item.previous || null; else gallery = gallery.filter(other => other !== item); return;
        }
        const data = new FormData(); data.append('photo',item.source);
        const blob = await send(root.dataset.prepareUrl,data,'blob',percent => { item.progress = percent; render(); });
        if (!present(item)) return;
        if (blob.size > rules.outputBytes) throw new Error(copy.batch);
        const file = new File([blob],item.name.replace(/\.[^.]+$/,'') + '.webp',{type:'image/webp'});
        item.optimizedHash = await digest(await file.arrayBuffer());
        if (items().some(other => other !== item && other.optimizedHash === item.optimizedHash)) {
          message(target,item.name,copy.duplicate); if (main === item) main = item.previous || null; else gallery = gallery.filter(other => other !== item); return;
        }
        item.objectUrl = await preview(file); item.preview = item.objectUrl;
        if (!present(item)) { release(item); return; }
        item.file = file; item.source = null; item.state = 'ready'; item.error = '';
        release(item.previous); item.previous = null;
      } catch (error) { item.state = 'error'; item.error = error.message || copy.failed; }
      finally { item.progress = null; sync(); render(); }
    }
    function enqueue(item,target) { queue = queue.then(() => prepare(item,target)).catch(() => { item.state = 'error'; item.error = copy.failed; render(); }); }
    function addFiles(files,target) {
      if (saving || busy) return;
      if (target === 'main' && files.length !== 1) { message(target,'',copy.one); return; }
      for (const file of files) {
        const format = extensions[file.name.split('.').pop().toLowerCase()];
        const reason = !format ? copy.format : !file.size || file.size > rules.sourceBytes ? copy.size : format === 'heif' && !rules.heif ? copy.heif : target === 'gallery' && gallery.length >= rules.maxGallery ? copy.full : '';
        if (reason) { message(target,file.name,reason); continue; }
        const item = {id:crypto.randomUUID(),name:file.name,source:file,state:'queued'};
        if (target === 'main') { if (blocking()) { message(target,file.name,copy.wait); continue; } item.previous = main; main = item; }
        else gallery.push(item);
        enqueue(item,target);
      }
      sync(); render();
    }
    async function materialize(item) {
      if (!item || item.file) return item;
      const response = await fetch(item.url, {credentials:'same-origin'});
      if (!response.ok) throw new Error(copy.failed);
      const blob = await response.blob();
      if (blob.size > rules.sourceBytes) throw new Error(copy.size);
      return {...item, savedId:null, file:new File([blob],item.name,{type:blob.type || 'image/webp'}), state:'ready'};
    }
    async function promote(item) {
      if (blocking() || saving) return;
      busy++; render();
      try {
        const selected = await materialize(item), previous = await materialize(main), index = gallery.indexOf(item);
        main = selected;
        if (previous) gallery[index] = previous; else gallery.splice(index,1);
        sync();
      } catch (error) { message('gallery',item.name,error.message || copy.failed); }
      finally { busy--; render(); }
    }
    async function save(submitter) {
      if (blocking()) { status.textContent = copy.wait; return {ok:false, errors:{gallery_images:[copy.wait]}}; }
      if (items().reduce((sum,item) => sum + (item.file?.size || 0),0) > rules.batchBytes) return {ok:false,errors:{gallery_images:[copy.batch]}};
      requestId ||= crypto.randomUUID(); saving = true;
      const data = new FormData(form); data.set('form_action',submitter?.value || 'save_draft'); data.set('photo_request_id',requestId);
      data.delete('photo'); data.delete('gallery_images');
      if (main?.file) data.append('photo', main.file);
      newFiles().forEach(item => data.append('gallery_images', item.file));
      const oldStates = new Map(items().map(item => [item,item.state]));
      items().forEach(item => { item.state = 'saving'; item.error = ''; }); render(); status.textContent = copy.saving;
      // Freeze edits so a retry uses exactly the same submitted state.
      const controls = [...form.querySelectorAll('input,select,textarea,button')].filter(node => !node.disabled);
      controls.forEach(node => { node.disabled = true; });
      try {
        const result = JSON.parse(await send(root.dataset.saveUrl,data,'text',percent => { status.textContent = `${copy.saving} ${percent}%`; }));
        if (!result.ok) throw Object.assign(new Error(copy.saveFailed), {errors:result.errors});
        items().forEach(item => { item.state = 'saved'; }); changedPhotos = false; render(); status.textContent = copy.saved;
        return result;
      } catch (error) {
        items().forEach(item => { item.state = item.file ? 'save-error' : oldStates.get(item); item.error = item.file ? copy.saveFailed : ''; });
        render(); status.dataset.savedError = '1'; status.textContent = copy.saveFailed;
        const retry = document.createElement('button'); retry.type = 'button'; retry.textContent = copy.retry; retry.addEventListener('click', () => form.requestSubmit(submitter)); status.append(' ', retry);
        return {ok:false, errors:error.errors || {gallery_images:[copy.saveFailed]}};
      } finally { saving = false; controls.forEach(node => { node.disabled = false; }); render(); }
    }
    root.querySelector('[data-photo-fallback-clear]').hidden = true;
    root.querySelector('[data-photo-fallback-delete]').hidden = true;
    root.querySelector('[data-photo-gallery-help]').textContent = copy.order;
    root.querySelectorAll('[data-photo-zone]').forEach(zone => {
      const target = zone.dataset.photoZone, field = zone.querySelector('input');
      zone.classList.add('pw-upload');
      const caption = document.createElement('div'); caption.className = 'pw-upload-caption'; caption.setAttribute('aria-hidden','true');
      const title = document.createElement('strong'), hint = document.createElement('span'); title.textContent = copy.choose; hint.textContent = copy.drop; caption.append(title,hint); zone.prepend(caption);
      field.addEventListener('change',() => { const files = [...field.files]; addFiles(files,target); });
      ['dragenter','dragover'].forEach(type => zone.addEventListener(type,event => { if (event.dataTransfer.types.includes('Files')) {event.preventDefault(); zone.classList.add('is-dragging');} }));
      zone.addEventListener('dragleave',() => zone.classList.remove('is-dragging'));
      zone.addEventListener('drop',event => { if (!event.dataTransfer.files.length) return; event.preventDefault(); event.stopPropagation(); zone.classList.remove('is-dragging'); addFiles([...event.dataTransfer.files],target); });
    });
    ['input','change'].forEach(type => form.addEventListener(type,() => { if (!saving) requestId = null; }));
    window.addEventListener('pagehide',event => { if (!event.persisted) items().forEach(item => { release(item); release(item.previous); }); });
    sync(false); render();
    const editor = {save, addFiles, hasMain:() => !!main && !['queued','preparing','error'].includes(main.state), preview:() => main?.preview || '', blocking, validationMessage:() => blocking() ? copy.wait : '', ready:() => queue};
    form.photoEditor = editor;
    return editor;
  }
  window.KidsMapPhotoEditor = {mount, signature, dimensions};
})();
