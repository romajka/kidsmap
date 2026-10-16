"""Aggregate fictional acceptance readback, explicit READ ONLY and timeouts."""
import hashlib,json
from pathlib import Path
from django.conf import settings
from django.db import connection,transaction
from catalog.models import Specialist,SpecialistDocument,SpecialistProposalDraft,SpecialistEmployment
P=Path(__file__).resolve().parent;R=P.parents[2];S=R/'.tmp/module03-spec-fix-2026-10-13-r1'
with transaction.atomic():
 with connection.cursor() as c:
  c.execute('SET TRANSACTION READ ONLY');c.execute("SET LOCAL statement_timeout='10s'");c.execute("SET LOCAL lock_timeout='2s'")
  c.execute('SHOW server_version');version=c.fetchone()[0]
 profiles={str(p.pk):{'status':p.status,'person_verified':bool(p.verified_person_user_id and p.person_verified_at),'author_is_person':p.created_by_id==p.verified_person_user_id if p.verified_person_user_id else False,'active_locations':p.practice_locations.filter(is_active=True).count(),'photo_exists':p.photo.storage.exists(p.photo.name) if p.photo else False} for p in Specialist.objects.all()}
 documents={'total':SpecialistDocument.objects.count(),'identity_public_count':SpecialistDocument.objects.filter(document_type='identity',is_published=True).count(),'baseline_corrupt_document_count':SpecialistDocument.objects.filter(name='SYNTHETIC corrupt RED').count()}
 proposals={'total':SpecialistProposalDraft.objects.count(),'submitted':SpecialistProposalDraft.objects.filter(submitted_at__isnull=False).count()}
 employments={'total':SpecialistEmployment.objects.count(),'active':SpecialistEmployment.objects.filter(status='active').count(),'cancelled':SpecialistEmployment.objects.filter(status='cancelled').count()}
original=(S/'assets/certificate.pdf').read_bytes();downloads={f.name:hashlib.sha256(f.read_bytes()).hexdigest()==hashlib.sha256(original).hexdigest() for f in (S/'assets').glob('download-*.pdf')}
result={'transaction':'READ ONLY','statement_timeout':'10s','lock_timeout':'2s','postgres':version,'profiles':profiles,'documents':documents,'proposals':proposals,'employments':employments,'genuine_download_bytes_match':downloads,'database_loopback':connection.settings_dict['HOST']=='127.0.0.1','cache':settings.CACHES['default']['BACKEND'],'email':settings.EMAIL_BACKEND,'sole_locale_root':str(settings.LOCALE_PATHS[0])}
(P/'readback.json').write_text(json.dumps(result,indent=2));print('Read-only fictional aggregate and6 native downloads recorded.')
