import json,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=R/'docs/qa/site-qa20-recheck-2026-10-18-pc-r1';Q=R/'.tmp/site20-pc-plan-r1';P=R/'docs/qa/site-qa22-fix-2026-10-18-pc-r1'
for d in [O,Q]:(d/'test_site20_candidate.py').write_bytes((R/'.tmp/site20-tests.py').read_bytes())
s=(P/'run_red.py').read_text()
for a,b in [('site22-pc-fix-r1','site20-pc-plan-r1'),('m10s22-fix-r1','m10s20-plan-r1'),('test_site22_candidate','test_site20_candidate')]:s=s.replace(a,b)
(O/'run_red.py').write_text(s)
s=(Q/'qa_urls.py').read_text().replace("'section_editor','section_viewer'","'section_editor','section_viewer','all_viewer','all_editor','gallery_adder','gallery_deleter'")
(Q/'qa_urls.py').write_text(s)
s=(Q/'seed.py').read_text()+'''
from catalog.models import SiteGalleryImage
models=('sitebrandingsettings','siteaboutsettings','sitecontactssettings','sitefootersettings','siteemptystatesettings','sitevisibilitysettings','siteanalytics','catalogcontentsettings','sitegalleryimage')
for role,codes in [('all_viewer',['view_'+m for m in models]),('all_editor',['change_'+m for m in models]),('gallery_adder',['add_sitegalleryimage']),('gallery_deleter',['view_sitegalleryimage','delete_sitegalleryimage'])]:
 user=get_user_model().objects.create_user('site08_'+role,role+'@example.invalid','fictional',is_staff=True)
 perms=Permission.objects.filter(content_type__app_label='catalog',codename__in=codes);assert perms.count()==len(codes);user.user_permissions.add(*perms)
SiteGalleryImage.objects.create(image=site.logo.name,title_ru='SITE20 synthetic gallery')
print('Four scoped actors and one synthetic gallery row added.')
'''
(Q/'seed.py').write_text(s)
(O/'prepare.py').write_bytes(Path(__file__).read_bytes())
cmd=['python3',str(O/'run_red.py')];r=subprocess.run(cmd);assert r.returncode==0
cmd=['python3',str(O/'normal_migrate.py')];r=subprocess.run(cmd);assert r.returncode==0
cmd=['python3',str(O/'start_server.py'),'red'];r=subprocess.run(cmd);assert r.returncode==0
