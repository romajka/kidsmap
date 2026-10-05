import hashlib, json, sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / 'qa'))
import add_demo_places as seed  # Sanitized settings and network/libpq guards, no seed main.
from django.db import transaction, connection
from catalog.models import Organization

prior = json.loads((HERE.parent / 'demo100/results.json').read_text())
with transaction.atomic():
    with connection.cursor() as cursor:
        cursor.execute('SET TRANSACTION READ ONLY')
    originals = list(seed.Place.objects.exclude(additional_info__startswith=seed.MARKER).order_by('pk').values())
    assert len(originals) == 3
    assert seed.digest(originals) == prior['existing_places_sha256']
    batch = seed.Place.objects.filter(additional_info__startswith=seed.MARKER)
    assert batch.count() == 100
    assert seed.public_place_queryset(seed.Place.objects.all()).count() == 103
    result = {'status': 'PASS', 'original_places': 3, 'original_fields_sha_unchanged': True,
              'demo_places': 100, 'public_places': 103, 'published_organizations': Organization.objects.filter(status='published').count(),
              'qa_draft_organizations': Organization.objects.filter(name_az__startswith='QA admin repair ',status='draft').count()}
(HERE / 'data-verification.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps(result))
