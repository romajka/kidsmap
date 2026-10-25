"""Read-only lifecycle verification for fictional browser role journeys."""
import argparse,json
from pathlib import Path
from environment import configure
p=argparse.ArgumentParser();p.add_argument('--profile-root',required=True);p.add_argument('--socket-dir',required=True);p.add_argument('--results',required=True,type=Path);p.add_argument('--sample-results',type=Path);args=p.parse_args()
configure(args.profile_root,args.socket_dir)
data=json.loads(args.results.read_text(encoding='utf-8'));assert data['synthetic']
rows=data['results'];assert rows and all(r['status']=='PASS' for r in rows)
required={'R_OWNER_RESUBMIT','R_OWNER_REJECT','R_CROSS_AUTHOR','R_ADMIN_DIRECT','R_REJECT','R_RETURN_RESUBMIT','R_PENDING_PRIVATE','R_MOD_FULL'};assert required <= {r['id'] for r in rows}
from django.db import connection,transaction
from catalog.models import Place,VolunteerPlaceRevision
checked=[]
with transaction.atomic():
    with connection.cursor() as cursor:
        cursor.execute('SET TRANSACTION READ ONLY');cursor.execute('SET LOCAL statement_timeout=20000');cursor.execute('SET LOCAL lock_timeout=2000')
    for role,marker,status in [('volunteer','R_REJECT','declined'),('owner','R_OWNER_RESUBMIT','approved'),('admin','R_ADMIN_DIRECT',None)]:
        row=next(r for r in reversed(rows) if r['id']==marker)
        place=Place.objects.select_related('owner','created_by').get(pk=row['placeId'])
        assert place.name_az.startswith(('Role journey volunteer ','Place E2E ')),role
        public=next(r for r in reversed(rows) if r['id']=='R_PUBLIC_SURFACES' and str(r['placeId'])==str(place.pk))
        assert place.name_az==public['name'] and place.status=='published' and place.is_active,role
        assert place.photo and place.photo.storage.exists(place.photo.name),role
        plans=list(place.pricing_plan_records.all());assert len(plans)==1 and plans[0].currency=='AZN',role
        assert plans[0].price== (150 if role=='volunteer' else 120),role
        assert plans[0].billing_interval=='month',role
        if role=='owner':assert place.owner.username=='place_owner'
        if role=='volunteer':assert place.owner_id is None and place.created_by.username=='place_volunteer'
        if status:
            revision=VolunteerPlaceRevision.objects.select_related('reviewed_by','author').get(place=place)
            assert revision.status==status and revision.reviewed_by.username=='place_admin' and revision.review_note,role
            assert revision.author.username==('place_owner' if role=='owner' else 'place_volunteer'),role
        checked.append(role)
    sample=None
    if args.sample_results:
        sample_data=json.loads(args.sample_results.read_text(encoding='utf-8'));assert sample_data['synthetic']
        sample_id=next(r['placeId'] for r in sample_data['results'] if r['id']=='R_VOL_DRAFT')
        sample_place=Place.objects.get(pk=sample_id,created_by__username='place_volunteer',owner__isnull=True)
        sample={'place_id':sample_place.pk,'pending':VolunteerPlaceRevision.objects.filter(place=sample_place,status='pending').exists() and not sample_place.is_public}
print(json.dumps({'synthetic':True,'read_only':True,'lifecycle':'PASS','roles':checked,'browser_records':len(rows),'manual_review_sample':sample}))
