"""Complete interrupted initial fictional taxonomy setup, before audited UI creation."""
import sys,json
sys.argv=['run.py','qa-seed'];from run import *
from django.contrib.auth import get_user_model
from django.db.migrations.recorder import MigrationRecorder
from catalog.models import Place,Category,SiteSettings
from catalog.testcases.utils import ensure_quality_subcategory
assert Place.objects.count()==1
actors={r:get_user_model().objects.get(username='qa01r_'+r) for r in ['owner','staff','admin','outsider','employee','specialist']}
cat=Category.objects.create(code='QA01R_LONG',name='QA01R '+('Long fictional category '*6),name_ru='QA01R '+('Длинная категория '*6),name_az='QA01R '+('Uzun uydurma kateqoriya '*6),name_en='QA01R '+('Long fictional category '*6))
sub=ensure_quality_subcategory(cat)
(HERE/'taxonomy.json').write_text(json.dumps({'category':cat.code,'subcategory':sub.pk}))
(HERE/'fixtures.json').write_text(json.dumps({'actors':{r:{'id':u.pk,'username':u.username,'email':u.email} for r,u in actors.items()},'ready_place':1,'settings':SiteSettings.objects.first().pk,'synthetic_only':True,'transition_entities_seeded':False},indent=2))
(HERE/'isolation.json').write_text(json.dumps({'python':sys.version.split()[0],'django':django.get_version(),'testing':settings.TESTING,'db':'place_recheck','db_port':'55446','cache':settings.CACHES['default'],'email':settings.EMAIL_BACKEND,'media':str(settings.MEDIA_ROOT),'private_media':str(settings.PRIVATE_MEDIA_ROOT),'migrations':MigrationRecorder.Migration.objects.count(),'external_integrations':False,'locale_paths':[str(p) for p in settings.LOCALE_PATHS]},indent=2))
print('Completed initial fictional fixtures, no audited transition performed')
