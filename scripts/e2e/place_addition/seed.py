"""Create fictional fixture data only after checking the actual isolated DB."""
import argparse
from io import BytesIO
import hashlib
import json
from pathlib import Path
from environment import configure,source_manifest

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--profile-root', required=True)
parser.add_argument('--socket-dir', required=True)
parser.add_argument('--output', required=True, type=Path)
parser.add_argument('--origin', default='http://127.0.0.1:8898')
args = parser.parse_args()
if not args.origin.startswith(('http://127.0.0.1:', 'http://localhost:')):
    parser.error('Only a loopback origin is permitted')
repository = configure(args.profile_root, args.socket_dir)
from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile
from django.db import transaction
from catalog.models import Place, PricingPlan
from catalog.services.pricing_plans import PRICING_STORAGE_FIELDS
from catalog.services.place_schedule import serialize_place_schedule
from catalog.testcases.utils import create_ready_place
from PIL import Image


def business_state(place):
    state = {field.name: str(getattr(place, field.name)) for field in Place._meta.fields
             if field.name not in {'updated_at', 'created_at', 'content_version'}}
    state['pricing'] = list(place.pricing_plan_records.order_by('id').values('id', *PRICING_STORAGE_FIELDS))
    state['schedule_days'] = serialize_place_schedule(place)
    state['gallery'] = list(place.gallery.order_by('order', 'id').values('id', 'image', 'order'))
    return json.loads(json.dumps(state, default=str))


args.output.parent.mkdir(parents=True, exist_ok=True)
images = []
for index, color in enumerate(['#136f38', '#e8b36b', '#5985a5']):
    data = BytesIO()
    Image.new('RGB', (640 + index * 10, 480), color).save(data, 'PNG')
    path = args.output.parent / f'photo-{index}.png'
    path.write_bytes(data.getvalue())
    images.append(path.name)

with transaction.atomic():
    User = get_user_model()
    users = {}
    for name, staff in [('place_admin', True), ('place_owner', False), ('place_other', False)]:
        user, created = User.objects.get_or_create(username=name, defaults={'email': name + '@example.invalid', 'is_staff': staff, 'is_superuser': staff, 'is_active': True})
        if created:
            user.set_password('LocalReview-2026!')
            user.save()
        users[name] = user
    fixtures = {}
    for key in ['direct', 'foreign', 'legacy', 'custom', 'draft']:
        name = f'Place QA 20261023 {key}'
        place = Place.objects.filter(name_az=name, owner=users['place_owner']).first()
        if place is None:
            place = create_ready_place(name_az=name, name_ru=name, name_en=name, owner=users['place_owner'], created_by=users['place_owner'])
            place.photo.save('qa-fixture.png', ContentFile((args.output.parent / images[0]).read_bytes()), save=True)
            if key == 'foreign':
                plan = place.pricing_plan_records.first()
                plan.product_type='membership'; plan.billing_mode='recurring'; plan.billing_interval='week'; plan.billing_interval_count=2; plan.currency='USD'; plan.quantity=7; plan.quantity_unit='visit'; plan.is_unlimited=False; plan.conditions_ru='Preserve fictional terms'; plan.save()
            if key == 'legacy':
                place.pricing_plan_records.all().delete()
                Place.objects.filter(pk=place.pk).update(price_per_lesson=35, price_from=35, price_to=35)
            if key == 'custom':
                Place.objects.filter(pk=place.pk).update(custom_price_badge_ru='Особая подтверждённая цена')
            if key == 'draft':
                Place.objects.filter(pk=place.pk).update(status='draft', is_active=False)
            place.refresh_from_db()
        fixtures[key] = {'id':place.pk, 'public':place.get_absolute_url(), 'state':business_state(place)}
    editor_fixtures={}
    for role in ['admin','owner']:
        editor_fixtures[role]={}
        for currency in ['USD','EUR']:
            name=f'Place QA 20261023 editor {role} {currency}'
            place=Place.objects.filter(name_az=name,owner=users['place_owner']).first()
            if place is None:
                place=create_ready_place(name_az=name,name_ru=name,name_en=name,
                    owner=users['place_owner'],created_by=users['place_owner'],
                    phone_country='US',phone1='+13104564918',whatsapp_mode='separate',whatsapp_number='+905321234567')
                plan=place.pricing_plan_records.first()
                plan.currency=currency;plan.product_type='membership';plan.billing_mode='recurring'
                plan.billing_interval='week';plan.billing_interval_count=2
                plan.quantity=7;plan.quantity_unit='visit';plan.is_active=currency=='USD';plan.save()
            editor_fixtures[role][currency]={'id':place.pk,'currency':currency}

contract_sources = ['static/js/kidsmap_pricing_editor.js', 'src/catalog/forms.py', 'src/catalog/domain_admin/place.py', 'src/catalog/templates/pages/includes/owner_place_continuous.html', 'src/catalog/templates/admin/catalog/place/change_form.html']
manifest = {'synthetic':True, 'database':'qa_stage04', 'origin':args.origin,
    'users':{name:{'username':user.username,'email':user.email,'password':'LocalReview-2026!'} for name,user in users.items()},
    'fixtures':fixtures, 'editor_fixtures':editor_fixtures, 'images':images,
    'sources':source_manifest(repository)}
args.output.write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
args.output.chmod(0o600)
print(json.dumps({'synthetic':True,'fixtures':len(fixtures),'users':len(users),'output':str(args.output)}))
