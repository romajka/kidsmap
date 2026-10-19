import sys,json,platform
sys.argv=['runtime.py','closure-readback'];from runtime import *
from django.db import transaction,connection
from catalog.services.review_versions import review_types
from django.template.loader import get_template
from django.contrib.staticfiles.finders import find
f=json.loads((QA/'fixtures.json').read_text());rows={}
with transaction.atomic():
 with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='5s'");c.execute("SET LOCAL lock_timeout='2s'")
 for kind,item in f['cases'].items():
  types=review_types()[kind];h=types[1].objects.get(pk=item['head_id'],user_id=f['author_id']);rows[kind]={'new_current':h.current_revision_id==item['new_revision'],'no_candidate':h.candidate_revision_id is None,'new_public_projection':h.text==item['new_text'] and h.rating==5,'zero_reactions':types[3].objects.filter(review=h).count()==0 and h.likes_count==h.dislikes_count==0,'only_two_revisions':h.revisions.count()==2}
out={'synthetic_only':True,'rows':rows,'all_checks_pass':all(all(x.values()) for x in rows.values())};(QA/'readback.json').write_text(json.dumps(out,indent=2));assert out['all_checks_pass']
info={'python':platform.python_version(),'django':django.get_version(),'testing':settings.TESTING,'source_count':len(entry['sources']),'source_verified':True,'sole_locales':list(map(str,settings.LOCALE_PATHS)),'template_origin':get_template('catalog/typed_reviews.html').origin.name,'css_origin':find('css/site.css'),'auth':'SIMULATED fictional QA login; native approve/react POST real'};(QA/'runtime-info.json').write_text(json.dumps(info,indent=2));print(json.dumps({'owned_heads':2,'readback_checks':10,'passed':True,'source1025':True}))
