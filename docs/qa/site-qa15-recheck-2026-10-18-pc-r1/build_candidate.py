import difflib,hashlib,json
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;C=O/'candidate'
sha=lambda b:hashlib.sha256(b).hexdigest()
messages=[
 ('Настройки изменились в другой вкладке. Ваш ввод не сохранён. Скопируйте нужные значения и откройте текущую версию отдельно.',
  'Settings changed in another tab. Your input has not been saved. Copy the values you need and open the current version separately.',
  'Parametrlər başqa vərəqdə dəyişdirilib. Daxil etdiyiniz məlumatlar yadda saxlanılmayıb. Lazım olan dəyərləri köçürün və cari versiyanı ayrıca açın.'),
 ('Открыть текущую версию в новой вкладке','Open the current version in a new tab','Cari versiyanı yeni vərəqdə aç'),
 ('Выбранные файлы нужно выбрать заново перед повторным сохранением.','Select your files again before saving another time.','Yenidən yadda saxlamazdan əvvəl faylları təkrar seçin.'),
]
site=R/'src/catalog/domain_admin/site.py';original=site.read_bytes();s=original.decode().replace('\r\n','\n')
s=s.replace('from django.contrib import admin\n','from django import forms\nfrom django.contrib import admin\nfrom django.core import signing\nfrom django.db import transaction\nimport hashlib\nimport json\n',1)
code='''_SETTINGS_REVISION_SALT = "catalog.site-settings-revision.v1"


def _settings_revision_payload(obj, actor):
    values = {field.name: field.value_to_string(obj)
              for field in obj._meta.concrete_fields}
    digest = hashlib.sha256(json.dumps(values, sort_keys=True).encode()).hexdigest()
    return {"row": obj.pk, "section": obj._meta.label_lower,
            "actor": actor, "digest": digest}


class _SettingsRevisionForm(forms.ModelForm):
    settings_revision_actor = None

    def clean(self):
        cleaned = super().clean()
        if self.instance.pk:
            try:
                payload = signing.loads(self.data.get("settings_revision", ""),
                                        salt=_SETTINGS_REVISION_SALT)
            except signing.BadSignature:
                payload = None
            if payload != _settings_revision_payload(self.instance, self.settings_revision_actor):
                self.settings_conflict = True
                raise forms.ValidationError(
                    _("Настройки изменились в другой вкладке. Ваш ввод не сохранён. Скопируйте нужные значения и откройте текущую версию отдельно."),
                    code="stale_settings",
                )
        return cleaned


'''
s=s.replace('class _BaseSiteSettingsSectionAdmin(admin.ModelAdmin):',code+'class _BaseSiteSettingsSectionAdmin(admin.ModelAdmin):',1)
s=s.replace('    change_form_template = "admin/catalog/shared_settings_change_form.html"','    form = _SettingsRevisionForm\n    change_form_template = "admin/catalog/shared_settings_change_form.html"',1)
methods='''    def get_queryset(self, request):
        queryset = super().get_queryset(request)
        # Django's admin changeform POST owns the surrounding transaction.
        return queryset.select_for_update() if request.method == "POST" else queryset

    def get_form(self, request, obj=None, change=False, **kwargs):
        base = super().get_form(request, obj, change=change, **kwargs)
        return type("ActorBoundSettingsForm", (base,),
                    {"settings_revision_actor": request.user.pk})

'''
s=s.replace('    def get_model_perms(self, request):\n',methods+'    def get_model_perms(self, request):\n',1)
before='''        return super().render_change_form(request, context, add=add, change=change, form_url=form_url, obj=obj)

    def _render_image_preview'''
after='''        form = context["adminform"].form
        context.setdefault("km_settings_title", self.model._meta.verbose_name.capitalize())
        context.setdefault("km_settings_subtitle", _("Заполните настройки для этого раздела сайта."))
        context.setdefault("km_settings_hub_url", reverse("admin:catalog_sitesettings_changelist"))
        context["km_settings_revision_enabled"] = True
        context["km_settings_revision"] = (request.POST.get("settings_revision", "")
            if request.method == "POST" else signing.dumps(
                _settings_revision_payload(obj, request.user.pk), salt=_SETTINGS_REVISION_SALT))
        context["km_settings_conflict"] = getattr(form, "settings_conflict", False)
        context["km_settings_current_url"] = request.path
        context["km_settings_reselect_files"] = bool(request.FILES)
        response = super().render_change_form(request, context, add=add, change=change, form_url=form_url, obj=obj)
        if context["km_settings_conflict"]:
            response.status_code = 409
        return response

    def _render_image_preview'''
assert before in s;s=s.replace(before,after,1)
# Share only the revision contract; keep subsection sidebar/title behavior local.
start=s.index('    def get_queryset(self, request):',s.index('class _BaseSiteSettingsSectionAdmin'))
end=s.index('    def get_model_perms(self, request):',start)
s=s[:start]+s[end:]
start=s.index('        form = context["adminform"].form',s.index('class _BaseSiteSettingsSectionAdmin'))
end=s.index('\n    def _render_image_preview',start)
revision_render=s[start:end]
s=s[:start]+'        return super().render_change_form(request, context, add=add, change=change, form_url=form_url, obj=obj)\n'+s[end:]
mixin='class _SiteSettingsConcurrencyAdminMixin:\n    form = _SettingsRevisionForm\n    change_form_template = "admin/catalog/shared_settings_change_form.html"\n\n'+methods+'    def render_change_form(self, request, context, add=False, change=False, form_url="", obj=None):\n'+revision_render+'\n\n'
s=s.replace('class _BaseSiteSettingsSectionAdmin(admin.ModelAdmin):',mixin+'class _BaseSiteSettingsSectionAdmin(_SiteSettingsConcurrencyAdminMixin, admin.ModelAdmin):',1)
s=s.replace('class SiteAnalyticsAdmin(admin.ModelAdmin):','class SiteAnalyticsAdmin(_SiteSettingsConcurrencyAdminMixin, admin.ModelAdmin):',1)
s=s.replace('class _BaseSiteSettingsSectionAdmin(_SiteSettingsConcurrencyAdminMixin, admin.ModelAdmin):\n    form = _SettingsRevisionForm\n','class _BaseSiteSettingsSectionAdmin(_SiteSettingsConcurrencyAdminMixin, admin.ModelAdmin):\n',1)
before='''                site = SiteSettings.get_solo()
                setattr(site, field_name, image_file)
                site.save()'''
after='''                with transaction.atomic():
                    site = SiteSettings.objects.select_for_update().get(pk=SiteSettings.get_solo().pk)
                    setattr(site, field_name, image_file)
                    site.save(update_fields=[field_name, "updated_at"])'''
assert before in s;s=s.replace(before,after,1)
start=s.index('            site = SiteSettings.get_solo()',s.index('    def ajax_delete_main_image'))
end=s.index('\n        except Exception as e:',start)
block=s[start:end];block=block.replace('site = SiteSettings.get_solo()','site = SiteSettings.objects.select_for_update().get(pk=SiteSettings.get_solo().pk)',1)
s=s[:start]+'            with transaction.atomic():\n'+''.join(('    '+line if line else '')+'\n' for line in block.splitlines()).rstrip('\n')+s[end:]
dest=C/site.relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(s.replace('\n','\r\n').encode() if b'\r\n' in original else s.encode())
path=R/'src/catalog/templates/admin/catalog/shared_settings_change_form.html';original=path.read_bytes();s=original.decode().replace('\r\n','\n')
s=s.replace('      {% csrf_token %}','      {% csrf_token %}\n      {% if km_settings_revision_enabled %}<input type="hidden" name="settings_revision" value="{{ km_settings_revision }}">{% endif %}',1)
s=s.replace('<div class="km-place-form-alert km-place-form-alert--danger">','<div class="km-place-form-alert km-place-form-alert--danger"{% if km_settings_conflict %} role="alert" tabindex="-1" autofocus{% endif %}>',1)
s=s.replace('            {{ adminform.form.non_field_errors }}','''            {{ adminform.form.non_field_errors }}
            {% if km_settings_conflict %}
              <p><a href="{{ km_settings_current_url }}" target="_blank" rel="noopener noreferrer">{% translate "Открыть текущую версию в новой вкладке" %}</a></p>
              {% if km_settings_reselect_files %}<p>{% translate "Выбранные файлы нужно выбрать заново перед повторным сохранением." %}</p>{% endif %}
            {% endif %}''',1)
dest=C/path.relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(s.replace('\n','\r\n').encode() if b'\r\n' in original else s.encode())
for lang in ['ru','az','en']:
 path=R/f'locale/{lang}/LC_MESSAGES/django.po';original=path.read_bytes();addition='\n'
 for ru,en,az in messages:
  assert ('msgid '+json.dumps(ru,ensure_ascii=False)) not in original.decode()
  addition+='\n#: catalog/domain_admin/site.py catalog/templates/admin/catalog/shared_settings_change_form.html\nmsgid '+json.dumps(ru,ensure_ascii=False)+'\nmsgstr '+json.dumps({'ru':ru,'en':en,'az':az}[lang],ensure_ascii=False)+'\n'
 dest=C/path.relative_to(R);dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(original+addition.encode())
files={p.relative_to(C).as_posix():{'before_sha256':sha((R/p.relative_to(C)).read_bytes()) if (R/p.relative_to(C)).exists() else None,'candidate_sha256':sha(p.read_bytes())} for p in C.rglob('*') if p.is_file()}
diff=b''
for path,d in files.items():
 before=(R/path).read_bytes() if d['before_sha256'] else b'';after=(C/path).read_bytes()
 diff+=b''.join(difflib.diff_bytes(difflib.unified_diff,before.splitlines(keepends=True),after.splitlines(keepends=True),fromfile=('a/'+path).encode() if before else b'/dev/null',tofile=('b/'+path).encode()))
(O/'proposed.diff').write_bytes(diff)
(O/'candidate-manifest.json').write_text(json.dumps({'applied':False,'files':files,'diff_sha256':sha(diff),'policy':'whole SiteSettings row409, bound text draft retained, no automatic merge or fresh token on stale POST','green':'NOT RUN; approval pending'},indent=2))
print(json.dumps({'candidate_files':len(files),'application_changes':0,'candidate_only':True}))
