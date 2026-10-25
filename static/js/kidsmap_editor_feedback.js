/* Explicit editor actions only. Background backups never call this module. */
(() => {
  'use strict';
  const running=new WeakMap(),consumed=new WeakSet(),initialMessages=new Set();
  const actions=new Set(['draft','save','moderation','publish']);
  const copy={
    ru:{draft:'Черновик сохранён',moderation:'Место отправлено на модерацию',publish:'Место опубликовано',draftBody:'Продолжить заполнение можно в своих черновиках. Место пока не опубликовано.',moderationBody:'Администратор проверит информацию перед публикацией.',publishBody:'Карточка доступна посетителям сайта.',validation:'Проверьте отмеченные поля',validationBody:'Исправьте подсказанные ошибки и повторите действие. Введённые данные остаются в форме.',conflict:'Карточка изменилась',conflictBody:'Откройте актуальную версию перед продолжением. Ваши изменения остаются в этой форме.',network:'Нет связи с сервером',networkBody:'Проверьте соединение и нажмите «Повторить». Подтверждение сохранения ещё не получено.',server:'Не удалось завершить действие',serverBody:'Сервер не подтвердил сохранение. Данные остаются в форме — попробуйте ещё раз.',pending:'Остались несохранённые изменения',pendingBody:'Дождитесь завершения сохранения и повторите действие.'},
    az:{draft:'Qaralama saxlanıldı',moderation:'Məkan moderasiyaya göndərildi',publish:'Məkan dərc olundu',draftBody:'Qaralamalarınızdan doldurmağa davam edə bilərsiniz. Məkan hələ dərc olunmayıb.',moderationBody:'Administrator məlumatı dərc etməzdən əvvəl yoxlayacaq.',publishBody:'Kart saytın ziyarətçilərinə açıqdır.',validation:'İşarələnmiş sahələri yoxlayın',validationBody:'Göstərilən xətaları düzəldib yenidən cəhd edin. Daxil edilmiş məlumatlar formada qalır.',conflict:'Kart dəyişib',conflictBody:'Davam etməzdən əvvəl cari versiyanı açın. Dəyişiklikləriniz bu formada qalır.',network:'Serverlə əlaqə yoxdur',networkBody:'Bağlantını yoxlayıb yenidən cəhd edin. Saxlanma hələ təsdiqlənməyib.',server:'Əməliyyat tamamlanmadı',serverBody:'Server saxlanmanı təsdiqləmədi. Məlumatlar formada qalır — yenidən cəhd edin.',pending:'Saxlanılmamış dəyişikliklər qalıb',pendingBody:'Saxlanmanın bitməsini gözləyib yenidən cəhd edin.'},
    en:{draft:'Draft saved',moderation:'Place sent for review',publish:'Place published',draftBody:'Continue from your drafts. This place is not published yet.',moderationBody:'An administrator will check the information before publication.',publishBody:'The listing is available to site visitors.',validation:'Check the highlighted fields',validationBody:'Correct the indicated errors and try again. Your entries remain in the form.',conflict:'This listing has changed',conflictBody:'Open the current version before continuing. Your changes remain in this form.',network:'Cannot reach the server',networkBody:'Check your connection and select Retry. Saving has not been confirmed yet.',server:'Could not complete the action',serverBody:'The server did not confirm saving. Your entries remain in the form — please try again.',pending:'Some changes are still unsaved',pendingBody:'Wait for saving to finish and try again.'}
  }[(document.documentElement.lang||'az').split('-')[0]];
  if(!copy)return;
  const savedCopy={ru:['Изменения сохранены','Обновлённые данные успешно сохранены.'],az:['Dəyişikliklər saxlanıldı','Yenilənmiş məlumatlar uğurla saxlanıldı.'],en:['Changes saved','Your updated information has been saved.']}[(document.documentElement.lang||'az').split('-')[0]];
  [copy.save,copy.saveBody]=savedCopy;
  const okText={ru:'Понятно',az:'Aydındır',en:'Got it'}[(document.documentElement.lang||'az').split('-')[0]];
  function classify(error){if(['validation','conflict','network','server','pending'].includes(error?.kind))return error.kind;if(error?.status===409||error?.conflict)return'conflict';if([400,422].includes(error?.status))return'validation';return error?.status?'server':'network';}
  function report(form,result){
    if(!actions.has(result?.action)||!['success','validation','conflict','network','server','pending'].includes(result?.outcome))return;
    const success=result.outcome==='success',key=success?result.action:result.outcome,title=copy[key],message=result.message||copy[key+'Body'];
    if(form?.dataset)form.dataset.editorFeedbackOutcome=result.outcome;
    const tone=success?'success':result.outcome==='validation'||result.outcome==='conflict'?'warning':'error';
    if(success&&['moderation','publish'].includes(result.action)&&window.kmModal?.alert)window.kmModal.alert({title,message,tone:'success',okText});
    else if(window.kmToast?.[tone])window.kmToast[tone](title,{message,duration:success?8000:0});
    else if(window.kmModal?.alert)window.kmModal.alert({title,message,tone:success?'success':'warning',okText});
    else {const note=document.createElement('p');note.setAttribute('role',success?'status':'alert');note.textContent=title+'. '+message;(form||document.body).prepend(note);}
  }
  function run(form,action,operation){
    if(running.has(form))return running.get(form);
    const busy=form.getAttribute('aria-busy'),buttons=[...form.querySelectorAll('[data-pc-save-draft],button[name="_save_draft"],button[name="action"][value="draft"],[data-pc-save-retry]')].map(button=>[button,button.disabled]);
    form.setAttribute('aria-busy','true');buttons.forEach(([button])=>button.disabled=true);
    let work;try{work=operation();}catch(error){work=Promise.reject(error);}
    const pending=Promise.resolve(work).then(result=>{const ok=result===true||result?.ok===true;report(form,{action,outcome:ok?'success':classify(result?.error||{kind:'server'})});return ok;},error=>{report(form,{action,outcome:classify(error)});return false;}).finally(()=>{if(busy===null)form.removeAttribute('aria-busy');else form.setAttribute('aria-busy',busy);buttons.forEach(([button,disabled])=>button.disabled=disabled);running.delete(form);});
    running.set(form,pending);return pending;
  }
  function consumeResults(initial=false){document.querySelectorAll('[data-km-editor-result]').forEach(node=>{if(consumed.has(node))return;consumed.add(node);const result={action:node.dataset.action,outcome:node.dataset.outcome,message:node.textContent.trim()},key=JSON.stringify(result);if(initial&&initialMessages.has(key))return;if(initial)initialMessages.add(key);report(null,result);});}
  window.KidsMapEditorFeedback={run,report,classify,consumeResults};
  document.addEventListener('km:submit-invalid',event=>{
    const form=event.target,button=event.detail?.submitter,outcome=event.detail?.outcome;
    if(!(form instanceof HTMLFormElement)||!['validation','pending'].includes(outcome))return;
    if(button&&button.form!==form)return;
    const action=button?.name==='_publish_place'?'publish':button?.name==='_save_draft'||button?.matches('[data-pc-save-draft]')||button?.value==='draft'||button?.value==='save_draft'?'draft':button?.value==='submit'||button?.value==='save_and_publish'?'moderation':'save';
    report(form,{action,outcome});
  });
  if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',()=>consumeResults(true),{once:true});else consumeResults(true);
})();
