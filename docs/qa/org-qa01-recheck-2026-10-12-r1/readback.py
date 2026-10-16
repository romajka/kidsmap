"""Own fictional organization only; bounded read-only transaction."""
import json
from pathlib import Path
from django.db import connection, transaction
from catalog.models import Organization, ServerDraft
HERE=Path(__file__).resolve().parent
entities=json.loads((HERE/'entities.json').read_text())
with transaction.atomic():
    with connection.cursor() as cursor:
        cursor.execute('SET TRANSACTION READ ONLY')
        cursor.execute("SET LOCAL statement_timeout='10s'")
        cursor.execute("SET LOCAL lock_timeout='2s'")
    org=Organization.objects.get(pk=entities['organization_id'])
    assert org.name_az.startswith('ORGQA01 fictional ')
    revision=org.content_revision
    data={'organization_id':org.pk,'public_id':str(org.public_id),'status':org.status,
          'content_version':org.content_version,'live_name_en':org.name_en,
          'revision_id':revision.pk,'revision_status':revision.status,
          'revision_version':revision.version,'revision_base_version':revision.base_content_version,
          'revision_name_en':revision.payload.get('name_en'),
          'drafts':list(ServerDraft.objects.filter(target_type='organization',target_id=org.pk)
                        .values('id','actor_id','source_version','schema_version','version','fields')),
          'read_only':True}
print(json.dumps(data,default=str))
