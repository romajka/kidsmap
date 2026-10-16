"""Initial fictional verified accounts only; deletion is exercised through native UI."""
from django.contrib.auth import get_user_model
from django.utils import timezone
from catalog.models import UserEmailVerification
from pathlib import Path
import json
password=json.loads((SCRATCH/'credentials.json').read_text())['login_password'];cells=[]
for lang in ('ru','az','en'):
 for width in(360,390,768,1024,1280,1440):
  username=f'qa06_{lang}_{width}';email=username+'@example.invalid'
  u=get_user_model().objects.create_user(username=username,email=email,password=password,first_name='Uydurma',last_name='Sınaq')
  UserEmailVerification.objects.create(user=u,email=email,is_verified=True,verified_at=timezone.now())
  cells.append({'lang':lang,'width':width,'email':email,'user_id':u.pk})
u=get_user_model().objects.create_user(username='qa06_red',email='qa06_red@example.invalid',password=password,first_name='Uydurma',last_name='Sınaq')
UserEmailVerification.objects.create(user=u,email=u.email,is_verified=True,verified_at=timezone.now())
(HERE/'fixtures.json').write_text(json.dumps({'cells':cells,'red':{'email':u.email,'user_id':u.pk},'initial_setup':'fictional verified fixtures, not a claim of native registration coverage'},indent=2))
print(json.dumps({'fictional_verified_fixtures':len(cells)+1}))
