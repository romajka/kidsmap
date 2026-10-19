import sys,json,subprocess
sys.path.insert(0,'/mnt/c/kidsmap/.tmp/m10-seq-r1')
from stage_apply import *
S=O/'stages/SITE14';n=json.loads((O/'evidence/browser-site14-baseline.json').read_text());assert len(n['rows'])==3 and sum(v is False for r in n['rows'] for v in r['checks'].values())==6 and not n['pageerrors']
path='src/catalog/templates/admin/catalog/shared_settings_change_form.html';t=(R/path).read_bytes().decode();nl='\r\n' if '\r\n' in t else '\n';old="{% static 'admin/js/kidsmap_admin_form_shell.js' %}";assert t.count(old)==1;t=t.replace(old,old+'?v=20261018_site14_r1')
anchor="  {% if opts.model_name == 'sitevisibilitysettings' %}";assert t.count(anchor)==1;t=t.replace(anchor,('  {% if km_settings_hub_url and has_change_permission %}\n  <link rel="stylesheet" href="{% static \'admin/css/pages/kidsmap_settings_draft.css\' %}">\n  <script src="{% static \'admin/js/kidsmap_settings_draft.js\' %}" defer></script>\n  {% endif %}\n').replace('\n',nl)+anchor)
anchor='      id="{{ opts.model_name }}_form"';assert t.count(anchor)==1;t=t.replace(anchor,anchor+nl+'      {% if km_settings_hub_url and has_change_permission %}data-settings-draft-owner="{{ request.user.pk }}" data-settings-draft-can-clear="{% if request.method == \'GET\' %}true{% else %}false{% endif %}"{% endif %}')
anchor='        {% if errors %}';assert t.count(anchor)==1
notice='''        {% if km_settings_hub_url and has_change_permission %}
        <div class="km-place-form-alert km-place-form-alert--warning km-settings-draft-notice" data-settings-draft-notice role="status" aria-live="polite" hidden>
          <strong>{% translate "Есть черновик ввода" %}</strong>
          <p>{% translate "Ввод хранится только в этой вкладке 30 минут. При восстановлении файлы выберите заново." %}</p>
          <div class="km-settings-draft-actions">
            <button type="button" class="km-btn--sidebar km-btn--draft" data-settings-draft-restore>{% translate "Восстановить ввод" %}</button>
            <button type="button" class="km-btn--sidebar km-btn--secondary-save" data-settings-draft-discard>{% translate "Удалить черновик" %}</button>
          </div>
        </div>
        {% endif %}

'''.replace('\n',nl);t=t.replace(anchor,notice+anchor)
shell='static/admin/js/kidsmap_admin_form_shell.js';raw=(R/shell).read_bytes().decode();snl='\r\n' if '\r\n' in raw else '\n'
old='''    setTimeout(function() {
      if (form) {
        initialSerializedForm = serializeForm(form);
      }
    }, 1000);'''.replace('\n',snl);assert raw.count(old)==1
new='''    if (form && form.hasAttribute("data-settings-draft-owner")) {
      initialSerializedForm = serializeForm(form);
    } else {
      setTimeout(function() {
        if (form) initialSerializedForm = serializeForm(form);
      }, 1000);
    }'''.replace('\n',snl);raw=raw.replace(old,new)
old='''            onExitWithoutSaving: function () {
              formSubmitted = true;'''.replace('\n',snl);assert raw.count(old)==1;raw=raw.replace(old,'''            onExitWithoutSaving: function () {
              form.dispatchEvent(new Event("km:discard-settings-draft"));
              formSubmitted = true;'''.replace('\n',snl))
css='''.km-settings-form-page [data-settings-draft-notice][hidden] { display: none !important; }
.km-settings-form-page .km-settings-draft-notice { display: block; min-width: 0; overflow-wrap: anywhere; }
.km-settings-draft-notice strong { display: block; }
.km-settings-draft-notice p { margin: 8px 0 12px; }
.km-settings-draft-actions { display: flex; flex-wrap: wrap; gap: 10px; }
.km-settings-draft-actions .km-btn--sidebar {
  flex: 1 1 160px; width: auto; min-height: 44px; padding: 10px 12px;
  white-space: normal; overflow-wrap: anywhere;
}
.km-settings-draft-actions button:focus-visible { outline: 3px solid #136f38; outline-offset: 3px; }
'''
files={path:t.encode(),shell:raw.encode(),'static/admin/js/kidsmap_settings_draft.js':(Q/'settings_draft_candidate.js').read_bytes(),'static/admin/css/pages/kidsmap_settings_draft.css':css.encode(),'src/catalog/testcases/test_site_qa14_settings_draft.py':(Q/'test_site14_candidate.py').read_bytes()}
msgs=['Есть черновик ввода','Ввод хранится только в этой вкладке 30 минут. При восстановлении файлы выберите заново.','Восстановить ввод','Удалить черновик']
translations={'ru':msgs,'az':['Daxil edilmiş məlumatların qaralaması var','Qaralama yalnız bu vərəqdə 30 dəqiqə saxlanılır. Bərpa zamanı faylları yenidən seçin.','Daxil edilmiş məlumatları bərpa et','Qaralamanı sil'],'en':['An input draft is available','The draft is kept in this tab for 30 minutes. Select files again when restoring it.','Restore input','Delete draft']}
for lang,values in translations.items():
 rel='locale/'+lang+'/LC_MESSAGES/django.po';before=(R/rel).read_bytes();text=before.decode();pnl='\r\n' if '\r\n' in text else '\n';extra=''
 for msg,value in zip(msgs,values):
  if ('msgid '+json.dumps(msg,ensure_ascii=False)) in text:
   assert msg=='Восстановить ввод'
   continue
  extra+='\n#: src/catalog/templates/admin/catalog/shared_settings_change_form.html\nmsgid '+json.dumps(msg,ensure_ascii=False)+'\nmsgstr '+json.dumps(value,ensure_ascii=False)+'\n'
 files[rel]=before+extra.replace('\n',pnl).encode()
apply('14',files)
cmd=['docker','exec','m10seq-r1-app','python',str(R/'scripts/build_isolated_locales.py'),'build','--source-locale',str(R/'locale'),'--output',str(Q/'locales-site14'),'--compiler','native'];p=subprocess.run(cmd,capture_output=True,text=True);(S/'evidence/locale-build.txt').write_text(p.stdout+p.stderr);assert p.returncode==0,p.stderr
stage=json.loads((Q/'stage.json').read_text());(S/'evidence/stage-before-locale.json').write_text(json.dumps(stage,indent=2));stage['locales']='locales-site14';(Q/'stage.json').write_text(json.dumps(stage));(S/'evidence/locale-build.json').write_text(json.dumps({'command':cmd,'exit':p.returncode,'isolated_locales':'az,ru,en','shared_MO_untouched':True},indent=2));print('SITE14 bounded public-settings input draft applied; no save/permission/revision semantics changed.')
