"""Rotate only synthetic users after diagnostic argv exposure; print no password."""
import json,secrets,os
from pathlib import Path
from django.conf import settings
from django.contrib.auth import get_user_model
P=Path(settings.QA_ROOT)/'credentials.json';data=json.loads(P.read_text());old=data['owner_password'];data['owner_password']=secrets.token_urlsafe(32)
P.write_text(json.dumps(data));os.chmod(P,0o600)
users=get_user_model().objects.filter(username__startswith='eventqa_')
count=0
for u in users:u.set_password(data['owner_password']);u.save(update_fields=['password']);count+=1
print(json.dumps({'own_fictional_password_rotated':True,'users':count,'production_credentials_used':False}))
