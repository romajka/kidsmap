"""Synthetic foreign baseline for cross-object denial; no audited transition is implemented here."""
import sys,json
sys.argv=['run.py','qa-foreign-fixture'];from run import *
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.files.base import ContentFile
from catalog.models import Specialist,SpecialistDocument
u=get_user_model().objects.get(username='qa_outsider')
p=Specialist.objects.create(name='Вымышленный чужой профиль',verified_person_user=u,person_verified_at=timezone.now(),owner=u,created_by=u,status='draft',consultation_format='online',bio_ru='Вымышленные закрытые сведения',phone='+994500000099')
doc=SpecialistDocument(specialist=p,document_type='identity',name='Вымышленный чужой документ');doc.file.save('identity.pdf',ContentFile((STATE/'assets/identity.pdf').read_bytes()),save=True)
(HERE/'foreign-fixture.json').write_text(json.dumps({'profile':p.pk,'document':doc.pk,'private_media_test_path':'/media/'+doc.file.name,'fixture_only':True}),encoding='utf-8')
print('Synthetic foreign baseline created',p.pk,doc.pk)
