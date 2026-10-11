import sys,json
sys.argv=['run.py','diagnostic']
from run import *
from django.test import Client
from django.test.utils import setup_test_environment
from django.contrib.auth import get_user_model
from django.core import signing
from catalog.models import Place
from catalog.services import publication
setup_test_environment()
c=Client();c.force_login(get_user_model().objects.get(username='qa_owner'))
out=[]
for pk in (1,2):
    r=c.get(f'/ru/account/places/{pk}/edit/')
    form=r.context['form'];token=form.initial['publication_token'];d=signing.loads(token,salt='publication-source');live=Place.objects.get(pk=pk);snap=publication.snapshot(live,'place')
    out.append({'id':pk,'http':r.status_code,'token_source_matches':d['source']==live.content_version,'snapshot_mismatch_keys':[k for k in snap if snap[k]!=d['snapshot'].get(k)],'dependencies_match':d['dependencies']==publication.dependencies(live,'place'),'gallery_preview_count':len(form.saved_gallery_preview)})
(HERE/'diagnostic.json').write_text(json.dumps(out,indent=2),encoding='utf-8');print(json.dumps(out))
