import json
from pathlib import Path
from django.contrib.auth import get_user_model
from catalog.models import Place
from django.utils.translation import override
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[2];secret=json.loads((ROOT/'.tmp'/HERE.name/'credentials.json').read_text())
U=get_user_model()
for pk in (3,4):
 u=U.objects.get(pk=pk)
 if not u.check_password(secret['owner_password']):u.set_password(secret['owner_password']);u.save(update_fields=['password'])
category=Place.objects.get(pk=1).category
p=Place.objects.create(name='QA14 close fictional foreign private',name_az='QA14 close fictional foreign private',owner_id=3,created_by_id=3,category=category,status='draft',is_active=False)
private=Place.objects.get(pk=1);urls={}
for lang in ('ru','az','en'):
 with override(lang):urls[lang]=private.get_absolute_url()
(HERE/'acl-fixture-ids.json').write_text(json.dumps({'own_private_id':private.pk,'foreign_id':p.pk,'private_urls':urls,'synthetic_only':True,'purpose':'fictional fixture setup only; checked native actions are never ORM transitions'}))
print('Own fictional negative ACL fixtures ready.')
