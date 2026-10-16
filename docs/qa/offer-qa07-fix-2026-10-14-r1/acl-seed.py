import json
from pathlib import Path
from django.contrib.auth import get_user_model
from catalog.models import ServerDraft
P=Path(__file__).resolve().parent;R=P.parents[2];s=json.loads((R/'.tmp'/P.name/'credentials.json').read_text());f=json.loads((P/'fixtures.json').read_text());u=get_user_model().objects.create_user('offerqa07_outsider',email='offerqa07_outsider@example.invalid',password=s['owner_password']);f['outsider_email']=u.email;f['private_draft_id']=str(ServerDraft.objects.filter(actor__username='offerqa07_owner',target_id=f['place']).order_by('-saved_at').first().pk);(P/'fixtures.json').write_text(json.dumps(f,indent=2));print('Own fictional outsider prerequisite only.')
