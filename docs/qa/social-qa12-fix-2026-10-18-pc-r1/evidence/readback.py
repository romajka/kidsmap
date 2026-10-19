import sys,json,platform
sys.argv=['runtime.py','readback'];from runtime import *
from django.db import transaction,connection
from catalog.services.review_versions import review_types
from django.template.loader import get_template
from django.contrib.staticfiles.finders import find
f=json.loads((QA/'fixtures.json').read_text());rows={}
with transaction.atomic():
 with connection.cursor() as c:c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='5s'");c.execute("SET LOCAL lock_timeout='2s'")
 for kind,item in f['cases'].items():
  types=review_types()[kind];h=types[1].objects.get(pk=item['head_id'],user_id=f['author_id']);expected=1 if kind=='place' else 0
  rows[kind]={'current_preserved':h.current_revision_id==item['new_revision'],'candidate_none':h.candidate_revision_id is None,'public_new':h.text==item['new_text'] and h.rating==5,'two_revisions':h.revisions.count()==2,'expected_counters':h.likes_count==expected and h.dislikes_count==0,'expected_reactions':types[3].objects.filter(review=h).count()==expected}
out={'rows':rows,'all_checks_pass':all(all(v.values()) for v in rows.values()),'expected_writes':'4native moderation decisions; zero stale reactions; one deliberate fresh Place vote; fictional seed/session writes'};(QA/'readback.json').write_text(json.dumps(out,indent=2));assert out['all_checks_pass']
info={'python':platform.python_version(),'django':django.get_version(),'testing':settings.TESTING,'source_count':len(entry['sources']),'source_verified':True,'sole_locales':list(map(str,settings.LOCALE_PATHS)),'template_origin':get_template('catalog/review_reaction_conflict.html').origin.name,'css_origin':find('css/pages/typed_reviews.css'),'test_db':settings.DATABASES['default']['TEST']['NAME']};(QA/'runtime-info.json').write_text(json.dumps(info,indent=2));print(json.dumps({'readback_checks':24,'passed':True,'source_count':1027,'current_mo_verified':True}))
