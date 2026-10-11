"""Initial fictional actors/taxonomy/assets and a ready connection target only."""
import sys,json
sys.argv=['run.py','qa-seed'];from run import *
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.migrations.recorder import MigrationRecorder
from catalog.models import *
from catalog.testcases.utils import create_ready_place
from PIL import Image,ImageDraw
U=get_user_model();assert U.objects.count()==0
pw=(STATE/'credential').read_text();actors={}
for role in ['owner','staff','admin','outsider','employee','specialist']:
 u=U.objects.create_user('qa01r_'+role,email=role+'01r@example.invalid',password=pw,first_name='Fictional QA01R',last_name=role,is_staff=role in ['staff','admin'],is_superuser=role=='admin')
 UserEmailVerification.objects.update_or_create(user=u,defaults={'email':u.email,'is_verified':True,'verified_at':timezone.now()})
 actors[role]=u
for name,size,color in [('fixture',(800,600),'#136F38'),('replacement',(800,600),'#efdcbd')]:
 im=Image.new('RGB',size,color);ImageDraw.Draw(im).text((20,20),'FICTIONAL QA01R '+name,fill='#111111');im.save(STATE/'assets'/f'{name}.png')
(STATE/'assets/bad.txt').write_text('fictional invalid image input')
media=Path(settings.MEDIA_ROOT)/'places/qa01r.png';media.parent.mkdir(parents=True,exist_ok=True);media.write_bytes((STATE/'assets/fixture.png').read_bytes())
ready=create_ready_place(name='Fictional QA01R ready connection',name_az='Uydurma QA01R hazir',name_ru='Вымышленное QA01R готовое место',name_en='Fictional QA01R ready connection',owner=actors['outsider'],created_by=actors['outsider'],photo='places/qa01r.png',status='published',lat=40.4,lng=49.8)
site=SiteSettings.objects.first() or SiteSettings();site.brand_name='Fictional QA01R';site.footer_email='support13@example.invalid';site.footer_phone='+994000000013';site.footer_whatsapp='https://example.invalid/qa01r-chat'
for f in site._meta.fields:
 if f.get_internal_type()=='FileField':setattr(site,f.name,'')
 if f.name.startswith(('home_title_','home_subtitle_','home_search_','home_cta_text_','contacts_text_','about_text_','empty_results_text_')):setattr(site,f.name,'')
site.save()
for g in SiteGalleryImage.objects.all():g.is_active=False;g.save()
from catalog.testcases.utils import ensure_quality_subcategory
cat=Category.objects.create(code='QA01R_LONG',name='QA01R '+'Long fictional category '*18,name_ru='QA01R '+'Длинная вымышленная категория '*18,name_az='QA01R '+'Uzun uydurma kateqoriya '*18,name_en='QA01R '+'Long fictional category '*18)
sub=ensure_quality_subcategory(cat)
(HERE/'taxonomy.json').write_text(json.dumps({'category':cat.code,'subcategory':sub.pk}))
(HERE/'fixtures.json').write_text(json.dumps({'actors':{r:{'id':u.pk,'username':u.username,'email':u.email} for r,u in actors.items()},'ready_place':ready.pk,'settings':site.pk,'synthetic_only':True,'transition_entities_seeded':False},indent=2))
(HERE/'isolation.json').write_text(json.dumps({'python':sys.version.split()[0],'django':django.get_version(),'testing':settings.TESTING,'db':'place_recheck','db_port':'55446','cache':settings.CACHES['default'],'email':settings.EMAIL_BACKEND,'media':str(settings.MEDIA_ROOT),'private_media':str(settings.PRIVATE_MEDIA_ROOT),'migrations':MigrationRecorder.Migration.objects.count(),'external_integrations':False},indent=2))
print('Initial fictional actors and ready connection target created; no audited transition seeded')
