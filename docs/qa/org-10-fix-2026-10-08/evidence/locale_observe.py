from pathlib import Path
import json
from django.utils.translation import override
from catalog.domain_admin.business import OrganizationForm
from catalog.controllers.organization_workspace import OrganizationCreateForm, OrganizationCandidateForm
s=Path(__file__).parent;rows=[];titles={'ru':('Название организации','Описание организации'),'az':('Təşkilatın adı','Təşkilatın təsviri'),'en':('Organization name','Organization description')}
for language in ('ru','az','en','ru'):
 with override(language):
  for cls in (OrganizationForm, OrganizationCreateForm, OrganizationCandidateForm):
   form=cls();labels={name:str(field.label) for name,field in form.fields.items() if name.startswith(('name_','description_'))}
   for name,label in labels.items():
    expected=titles[language][0 if name.startswith('name') else 1]+' ('+name[-2:].upper()+')';assert label==expected,(language,cls.__name__,name,label)
   rows.append({'language':language,'form':cls.__name__,'labels':labels})
  assert str(OrganizationForm.base_fields['name_az'].label)==titles[language][0]+' (AZ)'
(s/'locale-observe.json').write_text(json.dumps({'PASS':12,'rows':rows,'base_label_type':type(OrganizationForm.base_fields['name_az'].label).__name__},indent=2));print({'form_language_checks':12,'PASS':True})
