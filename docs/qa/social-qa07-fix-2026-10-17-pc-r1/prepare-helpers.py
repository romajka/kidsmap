from pathlib import Path
Q=Path(__file__).resolve().parent
(Q/'fixtures.py').write_text('''import json
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db import transaction
from django.utils import timezone
from catalog.models import Activity,Organization,Program
from catalog.services.public_presentation import present
from catalog.services.organization_ownership import request_join
from catalog.testcases.utils import create_ready_place
@transaction.atomic
def seed():
 U=get_user_model();assert not U.objects.filter(username='s07-fix-staff').exists()
 staff=U.objects.create_superuser('s07-fix-staff','staff@example.invalid',None)
 owner=U.objects.get(username='s07-author');place=Activity.objects.order_by('pk').first().place
 org=Organization.objects.create(owner=owner,created_by=owner,name_az='Fictional07 organization',status='published',approved_at=timezone.now())
 parent=create_ready_place(owner=owner,created_by=owner,name='Fictional07 program parent')
 request_join(actor=owner,place_id=parent.pk,organization_id=org.pk);parent.refresh_from_db()
 program=Program.objects.create(organization=org,name_az='Live AZ',name_ru='Live RU',name_en='Live EN',status='published',approved_at=timezone.now())
 rows=[]
 for variant,fields in [('escaping',dict(place=place,status='published',name_az='<script>fictional()</script> & class')),('empty',dict(place=place,status='published')),('hidden',dict(place=place,status='draft',name_az='PRIVATE DRAFT')),('liveprogram',dict(place=parent,status='published',program=program))]:
  a=Activity.objects.create(**fields);rows.append(dict(variant=variant,pk=a.pk,reviews=f'/reviews/activity/target/{a.pk}/',names={lang:present(a,lang)['name'] for lang in ['az','ru','en']}))
 (settings.QA_ROOT/'edge-targets.json').write_text(json.dumps(rows,ensure_ascii=False,indent=2))
 print('Own fictional edge fixtures created; no reviews or candidate records')
''')
p=Q/'qa_urls.py';t=p.read_text().replace("('author','guest')","('author','guest','staff')").replace("username='s07-author'","username='s07-fix-staff' if role=='staff' else 's07-author'");p.write_text(t)
(Q/'start-app.sh').write_text('''#!/bin/sh
set -eu
qa=/mnt/c/kidsmap/.tmp/social07-pc-fix-r1
docker exec m09s07-fix-r1-app python "$qa/runtime.py" seed > "$qa/seed.log" 2>&1
docker exec -d m09s07-fix-r1-app sh -c 'python /mnt/c/kidsmap/.tmp/social07-pc-fix-r1/runtime.py serve > /mnt/c/kidsmap/.tmp/social07-pc-fix-r1/server.log 2>&1'
''')
(Q/'tests.sh').write_text('''#!/bin/sh
set -u
qa=/mnt/c/kidsmap/.tmp/social07-pc-fix-r1
docker exec m09s07-fix-r1-app python "$qa/runtime.py" test catalog.testcases.test_social_qa07_activity_review_title.SocialQA07TitleTests catalog.testcases.test_social_qa03_conflict_recovery.TypedReviewConflictRecoveryTests.test_stale_draft_renders_with_latest_version_and_no_write catalog.testcases.test_social_qa03_conflict_recovery.TypedReviewConflictRecoveryTests.test_conflicting_script_text_is_escaped_and_preserved > "$qa/tests.log" 2>&1
result=$?
printf '%s\\n' "$result" > "$qa/tests.exit"
tail -n 19 "$qa/tests.log"
exit "$result"
''')
(Q/'run_json.py').write_text((Q.parent/'social06-pc-fix-r1/run_json.py').read_text())
print('Own edge fixture/routes/test11 helpers prepared')
