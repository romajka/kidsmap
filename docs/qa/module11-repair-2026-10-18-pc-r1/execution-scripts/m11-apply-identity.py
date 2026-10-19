import sys,json
sys.path.insert(0,'/mnt/c/kidsmap/.tmp/m11-full-r1')
from stage_apply import *
S=O/'stages/identity';n=json.loads((S/'evidence/red-r1.json').read_text());assert len(n['failures'])==4 and all('SpecialistStableIdentityTests' in v for v in n['failures']) and not n['errors'];(S/'IMPLEMENTATION_PLAN.md').write_text('# SEO05 stable specialist identity policy and repair\n\nAuthorized full module includes existing finding05, which permits immutable slug OR history/301. Choose stable immutable post-creation slug: existing published/shared addresses remain valid without database migration or guessed historical aliases. Names/bios remain editable, new profiles can choose a slug, partial unrelated writes retain behavior. Owner form does not expose slug; source service does not update it; existing admin exposes it and native baseline confirms input. No known production URLs are inferred or migrated.\n\nFresh25method RED has4identity failures:changed saved slug,cleared/regenerated slug,model validation,existing admin editable;21other controls including new sitemap/HEAD/landmarks/social/editor pass. Add model _validate_stable_slug reading original slug on correct DB, clean validation and pre-save validation only when slug would be written. Reject a changed nonempty existing slug using field ValidationError; do not silently replace user input. Existing blank legacy slug may still generate once. SpecialistAdmin get_readonly_fields appends slug only for existing object, preserving prior readonly fields and edit/create permission behavior. Append one clear validation message to3PO files. New8method test_module11_identity.py. Scope2application Python files+3PO+newtest; no models fields/schema/migration/alias table/route change. Compile fresh isolated locales before Django setup, sharedMO untouched. Native repeated name saves/reload and same old URL200 for3languages,readonlyslug/createfield and denied access, originals restored; compare current metadata/canonical/sitemap.\n')
p='src/catalog/models/specialist.py';t=(R/p).read_text();t=t.replace('from django.db import models','from django.db import models, router',1);t=t.replace('from django.conf import settings','from django.conf import settings\nfrom django.core.exceptions import ValidationError',1);start=t.index('class Specialist(models.Model)');pos=t.index('    def save(self, *args, **kwargs):',start);t=t[:pos]+'''    def _validate_stable_slug(self, using=None):
        if not self.pk:
            return
        database = using or self._state.db or router.db_for_read(type(self), instance=self)
        original_slug = type(self).objects.using(database).filter(pk=self.pk).values_list("slug", flat=True).first()
        if original_slug and self.slug != original_slug:
            raise ValidationError({"slug": _("Адрес существующего профиля нельзя изменить.")})

    def clean(self):
        super().clean()
        self._validate_stable_slug()

'''+t[pos:];pos=t.index('    def save(self, *args, **kwargs):',start);insert=pos+len('    def save(self, *args, **kwargs):\n');t=t[:insert]+'''        update_fields = kwargs.get("update_fields")
        if update_fields is None or "slug" in update_fields:
            self._validate_stable_slug(kwargs.get("using"))
'''+t[insert:]
q='src/catalog/domain_admin/specialist.py';u=(R/q).read_text();start=u.index('class SpecialistAdmin(');pos=u.index('    @admin.display',start);u=u[:pos]+'''    def get_readonly_fields(self, request, obj=None):
        fields = tuple(super().get_readonly_fields(request, obj))
        return fields + ("slug",) if obj is not None else fields

'''+u[pos:]
files={p:t.encode(),q:u.encode(),'src/catalog/testcases/test_module11_identity.py':(Q/'test_m11_identity_candidate.py').read_bytes()};message='Адрес существующего профиля нельзя изменить.'
for lang,text in {'ru':message,'az':'Mövcud profilin ünvanını dəyişmək olmaz.','en':'The address of an existing profile cannot be changed.'}.items():
 path='locale/'+lang+'/LC_MESSAGES/django.po';before=(R/path).read_bytes();assert ('msgid "'+message+'"').encode() not in before;files[path]=before+('\n\n#: catalog/models/specialist.py\nmsgid "'+message+'"\nmsgstr "'+text+'"\n').encode()
apply('identity',files,'stages/identity/evidence/red-r1.json')
