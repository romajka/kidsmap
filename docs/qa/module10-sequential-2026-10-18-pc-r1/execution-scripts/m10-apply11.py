import sys,json,subprocess
sys.path.insert(0,'/mnt/c/kidsmap/.tmp/m10-seq-r1')
from stage_apply import *
assert json.loads((O/'progress.json').read_text())['active']=='11'
S=O/'stages/SITE11';native=json.loads((O/'evidence/browser-site11-baseline.json').read_text());assert not native['errors'] and any(False in row['checks'].values() for row in native['rows'])
(S/'IMPLEMENTATION_PLAN.md').write_text('# SITE11 plan — ongoing immediate-fix authorization\n\nFresh native SIMULATED delayed/aborted chooser POST and delete-confirm/cancel show hardcoded RU feedback on EN/AZ; backend RED4methods7missinglocalized-payload observations, readonly control passes. Supply13public feedback strings through existing server gettext and json_script (no credentials/settings values); JS uses this localized payload for single/gallery loading, active/edit/delete labels, confirmation/buttons and network/server/upload/delete errors. Preserve native fetch payloads, permissions, loading/disabled/re-enable and destructive confirmation. Scope domain_admin/site.py,media change_list template,new4method regression,mediaJS,3PO; isolated current3localeMO, sharedMO untouched. Native fresh3languages6widths delayed/error/cancel preservation; gallery loader; real own-empty-banner upload and delayed delete (including localized deleting) then exact restoration. Existing SITE01/06/13/20 permission/upload/modal regression tests and syntax. External failure SIMULATED, actual successful upload/delete only owned fictional fixture. No schema/permission/config/production change.\n')
msgs={'loading':'Загрузка...','deleting':'Удаление...','delete_title':'Удалить изображение?','delete_message':'Загруженное изображение будет удалено без возможности восстановления.','confirm_delete':'Удалить','cancel':'Отмена','upload_error':'Не удалось загрузить файл','delete_error':'Не удалось удалить изображение','network_error':'Не удалось подключиться к серверу. Повторите попытку.','server_error':'Ошибка сервера','unknown_error':'Неизвестная ошибка','active':'Активно','edit':'Редактировать'}
english={'loading':'Loading...','deleting':'Deleting...','delete_title':'Delete image?','delete_message':'This uploaded image will be deleted permanently.','confirm_delete':'Delete','cancel':'Cancel','upload_error':'Could not upload file','delete_error':'Could not delete image','network_error':'Could not connect to the server. Please try again.','server_error':'Server error','unknown_error':'Unknown error','active':'Active','edit':'Edit'}
az={'loading':'Yüklənir...','deleting':'Silinir...','delete_title':'Şəkil silinsin?','delete_message':'Yüklənmiş şəkil həmişəlik silinəcək.','confirm_delete':'Sil','cancel':'Ləğv et','upload_error':'Faylı yükləmək mümkün olmadı','delete_error':'Şəkli silmək mümkün olmadı','network_error':'Serverə qoşulmaq mümkün olmadı. Yenidən cəhd edin.','server_error':'Server xətası','unknown_error':'Naməlum xəta','active':'Aktiv','edit':'Düzəliş et'}
path='src/catalog/domain_admin/site.py';t=(R/path).read_bytes().decode();nl='\r\n' if '\r\n' in t else '\n';anchor='            "can_change_main_images": request.user.has_perm("catalog.change_sitesettings"),';assert t.count(anchor)==1
block=nl+'            "site_media_i18n": {'+nl+''.join('                '+json.dumps(k)+': _('+json.dumps(v,ensure_ascii=False)+'),'+nl for k,v in msgs.items())+'            },';t=t.replace(anchor,anchor+block)
template='templates/admin/catalog/sitegalleryimage/change_list.html';h=(R/template).read_bytes().decode();hnl='\r\n' if '\r\n' in h else '\n';old="{% static 'admin/js/kidsmap_site_media.js' %}";assert h.count(old)==1;h=h.replace(old,old+'?v=20261018_site11_r1');anchor='<input type="hidden" id="km-csrf-token" value="{{ csrf_token }}">';assert h.count(anchor)==1;h=h.replace(anchor,anchor+hnl+'{{ site_media_i18n|json_script:"km-site-media-i18n" }}')
js='static/admin/js/kidsmap_site_media.js';j=(R/js).read_bytes().decode();jnl='\r\n' if '\r\n' in j else '\n'
prefix='''/* Localized server gettext payload; safe English fallback for an absent payload. */
const kmSiteMediaCopy = (() => {
    const fallback = __FALLBACK__;
    const node = document.getElementById("km-site-media-i18n");
    if (!node) return fallback;
    try { return Object.assign(fallback, JSON.parse(node.textContent)); }
    catch (_) { return fallback; }
})();
function kmSiteMediaError(error) {
    return error && error.name === "TypeError" ? kmSiteMediaCopy.network_error :
        (error && error.message) || kmSiteMediaCopy.unknown_error;
}

'''.replace('__FALLBACK__',json.dumps(english,ensure_ascii=False)).replace('\n',jnl);j=prefix+j
replacements={
 'Загрузка...':'${kmSiteMediaCopy.loading}',
 '`Ошибка сервера (${response.status})`':'`${kmSiteMediaCopy.server_error} (${response.status})`',
 '"Неизвестная ошибка"':'kmSiteMediaCopy.unknown_error',
 'title="Редактировать"':'title="${kmSiteMediaCopy.edit}"',
 'title="Удалить"':'title="${kmSiteMediaCopy.confirm_delete}"',
 '> Активно</span>':'> ${kmSiteMediaCopy.active}</span>',
 '`Не удалось загрузить файл «${file.name}»: ${err.message}`':'`${kmSiteMediaCopy.upload_error} «${file.name}»: ${kmSiteMediaError(err)}`',
 '`Не удалось загрузить файл "${file.name}": ${err.message}`':'`${kmSiteMediaCopy.upload_error} «${file.name}»: ${kmSiteMediaError(err)}`',
 '`Не удалось удалить изображение: ${err.message}`':'`${kmSiteMediaCopy.delete_error}: ${kmSiteMediaError(err)}`',
 "title: 'Удалить изображение?'":"title: kmSiteMediaCopy.delete_title",
 "message: 'Загруженное изображение будет удалено без возможности восстановления.'":"message: kmSiteMediaCopy.delete_message",
 "confirmText: 'Удалить'":"confirmText: kmSiteMediaCopy.confirm_delete",
 "cancelText: 'Отмена'":"cancelText: kmSiteMediaCopy.cancel",
 'window.confirm("Удалить загруженное изображение?")':'window.confirm(kmSiteMediaCopy.delete_title)'}
for old,new in replacements.items():assert old in j,old;j=j.replace(old,new)
lines=[];counts={'confirm_delete':0,'deleting':0}
for line in j.splitlines(True):
 stripped=line.strip();matched=False
 for label,key,icon in [('Удалить','confirm_delete','far fa-trash-alt'),('Удаление...','deleting','fas fa-spinner fa-spin')]:
  if stripped=="deleteBtn.innerHTML = '<i class=\""+icon+"\"></i> "+label+"';":
   indent=line[:len(line)-len(line.lstrip())];lines += [indent+"deleteBtn.innerHTML = '<i class=\""+icon+"\"></i> ';"+jnl,indent+'deleteBtn.appendChild(document.createTextNode(kmSiteMediaCopy.'+key+'));'+jnl];counts[key]+=1;matched=True;break
 if not matched:lines.append(line)
assert counts=={'confirm_delete':2,'deleting':1},counts;j=''.join(lines)
files={path:t.encode(),template:h.encode(),js:j.encode(),'src/catalog/testcases/test_site_qa11_media_feedback.py':(Q/'test_site11_candidate.py').read_bytes()}
for lang,translations in [('ru',msgs),('en',english),('az',az)]:
 rel='locale/'+lang+'/LC_MESSAGES/django.po';before=(R/rel).read_bytes();text=before.decode();pnl='\r\n' if '\r\n' in text else '\n';extra=''
 for key,msg in msgs.items():
  needle='msgid '+json.dumps(msg,ensure_ascii=False)
  if any(line==needle for line in text.splitlines()):continue
  extra+='\n#: src/catalog/domain_admin/site.py\n'+needle+'\nmsgstr '+json.dumps(translations[key],ensure_ascii=False)+'\n'
 files[rel]=before+extra.replace('\n',pnl).encode()
apply('11',files)
cmd=['docker','exec','m10seq-r1-app','python',str(R/'scripts/build_isolated_locales.py'),'build','--source-locale',str(R/'locale'),'--output',str(Q/'locales-site11'),'--compiler','native'];p=subprocess.run(cmd,capture_output=True,text=True);(S/'evidence/locale-build.txt').write_text(p.stdout+p.stderr);assert p.returncode==0,p.stderr
stage=json.loads((Q/'stage.json').read_text());stage['locales']='locales-site11';(Q/'stage.json').write_text(json.dumps(stage));(S/'evidence/locale-build.json').write_text(json.dumps({'command':cmd,'exit':p.returncode,'shared_MO_untouched':True},indent=2));print('SITE11 localized media feedback applied; isolated current3catalogues built.')
