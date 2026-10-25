"""Extend an already attested fictional QA fixture; never reseed places."""
import argparse,json
from pathlib import Path
from environment import configure,source_manifest
p=argparse.ArgumentParser();p.add_argument('--profile-root',required=True);p.add_argument('--socket-dir',required=True);p.add_argument('--fixture',type=Path,required=True);p.add_argument('--output',type=Path,required=True);args=p.parse_args()
repository=configure(args.profile_root,args.socket_dir)
fixture=json.loads(args.fixture.read_text(encoding='utf-8'))
assert fixture['synthetic'] and fixture['database']=='qa_stage04'
assert not args.output.exists(),'Preserve previous role fixture'
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from catalog.services.staff_roles import VOLUNTEER_GROUP
from django.db import transaction
with transaction.atomic():
    group,_=Group.objects.get_or_create(name=VOLUNTEER_GROUP)
    for name in ('place_volunteer','place_volunteer_other'):
        user,created=get_user_model().objects.get_or_create(username=name,defaults={'email':name+'@example.invalid','is_staff':True,'is_active':True})
        assert user.is_staff and not user.is_superuser and user.email.endswith('@example.invalid')
        if created:user.set_password(fixture['users']['place_admin']['password']);user.save()
        user.groups.add(group)
        fixture['users'][name]={'username':name,'email':user.email,'password':fixture['users']['place_admin']['password']}
fixture['sources']=source_manifest(repository)
args.output.write_text(json.dumps(fixture,ensure_ascii=False,indent=2),encoding='utf-8');args.output.chmod(0o600)
print(json.dumps({'synthetic':True,'volunteers':2,'new_place_fixtures':0}))
