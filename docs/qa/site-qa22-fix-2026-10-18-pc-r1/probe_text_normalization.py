import hashlib,json,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site22-pc-fix-r1'
code='''import sys,json
from pathlib import Path
Q=Path('/mnt/c/kidsmap/.tmp/site22-pc-fix-r1');sys.path.insert(0,str(Q));sys.argv=['runtime.py','probe'];from runtime import *
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.test import RequestFactory
from catalog.models import SiteSettings,SiteAboutSettings
request=RequestFactory().get('/admin/catalog/siteaboutsettings/1/change/');request.user=get_user_model().objects.get(username='site08_super');site=SiteSettings.objects.get(pk=1);form=admin.site._registry[SiteAboutSettings].get_form(request,obj=site,change=True)
data={}
for lang in ['ru','az','en']:
 name='about_text_'+lang;raw='QA '+lang+' synthetic paragraph. '*10;field=form.base_fields[name];actual=getattr(site,name);data[name]={'strip':field.strip,'raw_seed':raw,'cleaned_seed':field.clean(raw),'actual':actual,'actual_matches_form_cleaned_seed':actual==field.clean(raw)}
print(json.dumps(data))
'''
(Q/'normalization_probe.py').write_text(code);cmd=['docker','exec','m10s22-fix-r1-app','python',str(Q/'normalization_probe.py')];r=subprocess.run(cmd,capture_output=True,text=True);assert r.returncode==0,r.stderr[-500:];data=json.loads(r.stdout)
assert all(d['strip'] and d['actual_matches_form_cleaned_seed'] and d['raw_seed'].endswith(' ') and d['cleaned_seed']==d['raw_seed'][:-1] for d in data.values())
rel='src/catalog/domain_admin/site.py';before=(O/'entry-source'/rel).read_bytes();after=(R/rel).read_bytes();extra=b'    def response_post_save_change(self, request, obj):\r\n        """Exit a saved subsection to the existing settings hub."""\r\n        return redirect(reverse("admin:catalog_sitesettings_changelist"))\r\n\r\n';assert after.count(extra)==1 and after.replace(extra,b'',1)==before
result={'command':cmd,'exit':r.returncode,'about_fields':data,'source_outside_exact_response_hook_byte_identical_to_prepatch':True,'classification':'Existing Django CharField(strip=True) normalization, inferred pre-existing from unchanged form code/installed Django and observed in actual native saves; not a redirect/CSS regression','restoration_policy':'Own about-text content restored through native form validation to cleaned seed; no raw trailing-whitespace byte restoration claimed','initial_final_guard_failure':'Compared final normalized fixture to raw ORM seed; keep exact checks for all other values and media; qualify only this demonstrated normalization.'};(O/'evidence/text-normalization.json').write_text(json.dumps(result,ensure_ascii=False,indent=2));print(json.dumps({'all3_about_fields_normalized_as_existing_form':True,'form_code_unchanged':True,'application_refinements':0},indent=2))
