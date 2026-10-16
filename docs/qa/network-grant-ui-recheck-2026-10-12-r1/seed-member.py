"""Only fictional account fixture setup; no invitation or grant transitions."""
import json
from pathlib import Path
from django.contrib.auth import get_user_model
HERE=Path(__file__).resolve().parent
ROOT=HERE.parents[2]
secret=json.loads((ROOT/'.tmp'/HERE.name/'credentials.json').read_text())
user=get_user_model().objects.create_user(
    username='network_ui_member',email='network-ui-member@example.invalid',password=secret['owner_password'],
)
fixtures=json.loads((HERE/'fixtures.json').read_text())
fixtures['actors']['member']={'id':user.pk,'username':user.username,'email':user.email}
(HERE/'fixtures.json').write_text(json.dumps(fixtures))
print(json.dumps({'fictional_member_id':user.pk,'invitation_and_grant_created':False}))
