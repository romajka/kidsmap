"""Read-only preservation check against owned synthetic fixtures after E2E."""
import argparse
import json
from pathlib import Path
from environment import configure

parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--profile-root',required=True)
parser.add_argument('--socket-dir',required=True)
parser.add_argument('--fixture',required=True,type=Path)
parser.add_argument('--results',required=True,type=Path)
args=parser.parse_args()
configure(args.profile_root,args.socket_dir)
manifest=json.loads(args.fixture.read_text(encoding='utf-8'))
if manifest.get('synthetic') is not True or manifest.get('database')!='qa_stage04':raise RuntimeError('Synthetic fixture manifest required')
results=json.loads(args.results.read_text(encoding='utf-8'))
if not results.get('results') or any(row.get('status')!='PASS' for row in results['results']):raise RuntimeError('E2E results contain a failure or no tests')
from django.db import connection,transaction
from catalog.models import Place,VolunteerPlaceRevision
from catalog.services.pricing_plans import PRICING_STORAGE_FIELDS
from catalog.services.place_schedule import serialize_place_schedule
# These are the only deliberate edits made to the preservation fixtures by E05/E10.
# Audit timestamps/content_version were excluded explicitly when seeding, not here.
allowed_contact_edits={'phone2','whatsapp_mode','whatsapp_number'}
protected=[field.name for field in Place._meta.fields if field.name not in
           allowed_contact_edits | {'created_at','updated_at','content_version'}]
checked=[]
with transaction.atomic():
    with connection.cursor() as cursor:
        cursor.execute('SET TRANSACTION READ ONLY')
        cursor.execute('SET LOCAL statement_timeout=20000')
        cursor.execute('SET LOCAL lock_timeout=2000')
    for key,fixture in manifest['fixtures'].items():
        place=Place.objects.get(pk=fixture['id'])
        if place.owner.username!='place_owner' or not place.name_az.startswith('Place QA 20261023 '):raise RuntimeError('Fixture ownership mismatch')
        before=fixture['state']
        for field in protected:
            if field=='public_links' and field not in before:
                if place.public_links!=[]:raise AssertionError(f'{key}: new public links must retain the empty migration default')
                continue
            if str(getattr(place,field))!=before[field]:raise AssertionError(f'{key}: protected field changed: {field}')
        plans=json.loads(json.dumps(list(place.pricing_plan_records.order_by('id').values('id',*PRICING_STORAGE_FIELDS)),default=str))
        if plans!=before['pricing']:raise AssertionError(f'{key}: stored tariff business values or IDs changed')
        if serialize_place_schedule(place)!=before['schedule_days']:raise AssertionError(f'{key}: structured schedule changed')
        gallery=list(place.gallery.order_by('order','id').values('id','image','order'))
        if gallery!=before['gallery']:raise AssertionError(f'{key}: stored gallery changed')
        revision=VolunteerPlaceRevision.objects.filter(place=place,status__in=['draft','pending','rejected']).first()
        if revision and 'pricing_plans' in revision.payload:
            old_by_id={row['id']:row for row in before['pricing']}
            if {row.get('id') for row in revision.payload['pricing_plans']}!=set(old_by_id):raise AssertionError(f'{key}: candidate lost tariff IDs')
            for row in revision.payload['pricing_plans']:
                original=old_by_id[row['id']]
                for field in PRICING_STORAGE_FIELDS:
                    if field=='verified_at' and field not in row:continue
                    if field in row and str(row[field])!=str(original[field]):raise AssertionError(f'{key}: candidate changed hidden tariff field: {field}')
        checked.append(key)
print(json.dumps({'synthetic':True,'read_only':True,'fixture_preservation':'PASS','checked':checked,'browser_records':len(results['results'])}))
