"""Read only our isolated fictional fixtures; store aggregates/booleans."""
import sys,runpy,json
from pathlib import Path
P=Path(__file__).resolve().parent;sys.argv=[str(P/'run.py'),'qa-observe-no-action'];runpy.run_path(str(P/'run.py'))
from django.db.models import Count
from catalog.models import Specialist,SpecialistDocument,SpecialistProposalDraft
from django.contrib.auth import get_user_model
person=Specialist.objects.get(pk=1);bad=SpecialistDocument.objects.get(pk=7)
data={'specialists_count':Specialist.objects.count(),'documents_count':SpecialistDocument.objects.count(),'proposal_drafts_count':SpecialistProposalDraft.objects.count(),'specialist_status_counts':list(Specialist.objects.values('status').annotate(count=Count('id'))),'document_status_counts':list(SpecialistDocument.objects.values('status').annotate(count=Count('id'))),'profile1':{'published':person.status=='published','verified_person_is_different_from_author':person.created_by_id!=person.verified_person_user_id,'experience_is_zero':person.experience_years==0,'photo_file_exists':person.photo.storage.exists(person.photo.name),'bio_az_present':bool(person.bio_az),'bio_ru_present':bool(person.bio_ru),'bio_en_present':bool(person.bio_en)},'corrupt_document7':{'status':bad.status,'size':bad.file.size,'private_file_exists':bad.file.storage.exists(bad.file.name)},'review_permission_after_ui_role_change':get_user_model().objects.get(pk=6).has_perm('catalog.review_specialist_documents'),'only_synthetic_data':True,'mutations':'NONE; read-only aggregate observation'}
(P/'final-fixture-state.json').write_text(json.dumps(data,indent=2),encoding='utf-8');print('Own fixture state saved; no audited transition via ORM')
