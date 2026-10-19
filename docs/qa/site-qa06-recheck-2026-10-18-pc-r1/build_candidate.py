import difflib,hashlib,json,re
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;C=O/'candidate'
def save(rel,s,crlf=False):
 p=C/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(s.replace('\n','\r\n').encode() if crlf else s.encode())
p=R/'src/catalog/domain_admin/site.py';original=p.read_bytes();s=original.decode().replace('\r\n','\n')
s=s.replace('from django.core.exceptions import PermissionDenied', 'from django.core.exceptions import PermissionDenied, ValidationError\nfrom django.core.files.uploadedfile import UploadedFile',1)
s=s.replace('from catalog.services.admin_analytics import build_statistics_context','from catalog.services.admin_analytics import build_statistics_context\nfrom catalog.services.site_media_validation import validate_site_media_upload',1)
old='''                    code="stale_settings",
                )
        return cleaned'''
new='''                    code="stale_settings",
                )
        for name, field in self.fields.items():
            upload = cleaned.get(name)
            if isinstance(field, forms.FileField) and isinstance(upload, UploadedFile):
                try:
                    validate_site_media_upload(upload, field=name)
                except ValidationError as exc:
                    self.add_error(name, exc)
        return cleaned'''
assert old in s;s=s.replace(old,new,1)
insert='''class _SiteGalleryMediaForm(forms.ModelForm):
    def clean(self):
        cleaned = super().clean()
        upload = cleaned.get("image")
        if isinstance(upload, UploadedFile):
            try:
                validate_site_media_upload(upload, placement=cleaned.get("placement"))
            except ValidationError as exc:
                self.add_error("image", exc)
        return cleaned


'''
old='@admin.register(SiteGalleryImage)\nclass SiteGalleryImageAdmin(admin.ModelAdmin):';assert old in s;s=s.replace(old,insert+old+'\n    form = _SiteGalleryMediaForm',1)
old='''        try:
            from django.template.defaultfilters import filesizeformat
            import os'''
new='''        if field_name and field_name not in self.MAIN_IMAGE_FIELDS:
            return JsonResponse({"success": False, "error": "Invalid field name"}, status=400)
        if not field_name:
            if not placement:
                return JsonResponse({"success": False, "error": "Missing placement or field parameter"}, status=400)
            if placement not in {value for value, _ in SiteGalleryImage.PLACEMENT_CHOICES}:
                return JsonResponse({"success": False, "error": str(_("Укажите допустимый раздел галереи."))}, status=400)
        try:
            validate_site_media_upload(image_file, field=field_name, placement=placement if not field_name else None)
        except ValidationError as exc:
            return JsonResponse({"success": False, "error": " ".join(exc.messages)}, status=400)

        try:
            from django.template.defaultfilters import filesizeformat
            import os'''
assert s.count(old)==1;s=s.replace(old,new,1)
old='''                if field_name not in self.MAIN_IMAGE_FIELDS:
                    return JsonResponse({"success": False, "error": "Invalid field name"}, status=400)
                
''';assert old in s;s=s.replace(old,'',1)
old='''            if not placement:
                return JsonResponse({"success": False, "error": "Missing placement or field parameter"}, status=400)
                
''';assert old in s;s=s.replace(old,'',1)
save(p.relative_to(R),s,b'\r\n' in original)
p=R/'src/catalog/templates/admin/catalog/shared_settings_change_form.html';original=p.read_bytes();s=original.decode().replace('\r\n','\n')
s=s.replace('{% if km_settings_conflict %} role="alert" tabindex="-1" autofocus{% endif %}', ' role="alert" tabindex="-1" autofocus',1)
start=s.index('            {% else %}\n              <strong>{% translate "Форма содержит ошибки" %}')
end=s.index('            {% endif %}\n          </div>',start)
original_plural_block=re.search(r'{% blocktranslate count counter=errors\|length %}.*?{% endblocktranslate %}',s[start:end],re.S).group()
generic='''            {% else %}
              <span class="km-place-form-alert__icon" aria-hidden="true">!</span>
              <div class="km-place-form-alert__content">
                <strong class="km-place-form-alert__heading">{% translate "Форма содержит ошибки" %}.</strong>
                <span class="km-place-form-alert__description">
                  {% blocktranslate count counter=errors|length %}
                    Исправьте проблему ниже и сохраните карточку ещё раз.
                  {% plural %}
                    Исправьте проблемы ниже и сохраните карточку ещё раз.
                  {% endblocktranslate %}
                </span>
                {{ adminform.form.non_field_errors }}
              </div>
'''
generic=re.sub(r'{% blocktranslate count counter=errors\|length %}.*?{% endblocktranslate %}',lambda _:original_plural_block,generic,flags=re.S)
s=s[:start]+generic+s[end:];save(p.relative_to(R),s,b'\r\n' in original)
p=C/'src/catalog/services/site_media_validation.py';s=p.read_text()
for name in ['_INVALID','_BIG','_DIMENSIONS','_SVG']:
 lines=s.splitlines();s='\n'.join(line.replace(name+' = ',name+' = _(')+')' if line.startswith(name+' = ') and not line.startswith(name+' = _(') else line for line in lines)+'\n';s=s.replace('_('+name+')',name)
p.write_text(s)
messages=[
('Загрузите корректный JPG, PNG или WebP. SVG разрешён только для логотипа и партнёров.', 'Upload a valid JPG, PNG or WebP. SVG is allowed only for the logo and partners.', 'Düzgün JPG, PNG və ya WebP yükləyin. SVG yalnız loqo və tərəfdaşlar üçün icazəlidir.'),
('Файл слишком большой. Максимум: %(limit)s КБ.', 'The file is too large. Maximum: %(limit)s KB.', 'Fayl çox böyükdür. Maksimum: %(limit)s KB.'),
('Изображение слишком большое: максимум 12000 пикселей по стороне и 50 мегапикселей.', 'The image is too large: at most 12000 pixels per side and 50 megapixels.', 'Şəkil çox böyükdür: hər tərəf ən çox 12000 piksel, ümumi ölçü isə 50 meqapiksel olmalıdır.'),
('SVG должен быть статичным и не содержать скриптов, внешних ресурсов или встроенных изображений.', 'SVG must be static and contain no scripts, external resources or embedded images.', 'SVG statik olmalı, skriptlər, xarici resurslar və ya daxil edilmiş şəkillər ehtiva etməməlidir.'),
('Укажите допустимый раздел галереи.', 'Choose a valid gallery section.', 'Qalereyanın düzgün bölməsini seçin.'),
]
for lang in ['ru','az','en']:
 rel=Path(f'locale/{lang}/LC_MESSAGES/django.po');before=(R/rel).read_bytes();addition='\n'
 for ru,en,az in messages:
  addition+='\n#: catalog/services/site_media_validation.py catalog/domain_admin/site.py\n'
  if '%(limit)s' in ru:addition+='#, python-format\n'
  addition+='msgid '+json.dumps(ru,ensure_ascii=False)+'\nmsgstr '+json.dumps({'ru':ru,'az':az,'en':en}[lang],ensure_ascii=False)+'\n'
 (C/rel).parent.mkdir(parents=True,exist_ok=True);(C/rel).write_bytes(before+addition.encode())
sha=lambda b:hashlib.sha256(b).hexdigest()
files={p.relative_to(C).as_posix():{'before_sha256':sha((R/p.relative_to(C)).read_bytes()) if (R/p.relative_to(C)).exists() else None,'candidate_sha256':sha(p.read_bytes())} for p in C.rglob('*') if p.is_file()};assert len(files)==7
diff=[]
for rel in sorted(files):
 before=(R/rel).read_bytes().decode().splitlines(True) if (R/rel).exists() else [];after=(C/rel).read_bytes().decode().splitlines(True)
 diff.extend(difflib.unified_diff(before,after,fromfile='a/'+rel if (R/rel).exists() else '/dev/null',tofile='b/'+rel))
(O/'proposed.diff').write_bytes(''.join(diff).encode())
(O/'candidate-manifest.json').write_text(json.dumps({'applied':False,'files':files,'diff_sha256':sha((O/'proposed.diff').read_bytes()),'green':'NOT RUN; approval pending','policy':'Admin-only pre-storage validation; static raster+restricted static SVG; preserve bytes/current media on rejection; seven-file plan'},indent=2))
print(json.dumps({'candidate_files':7,'candidate_applied':False,'new_messages_each_locale':5,'scope':list(files)},indent=2))
