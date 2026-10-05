"""Add 100 marked synthetic places to the owned local preview, never reset it.

Run without arguments for inspection; --apply creates missing rows atomically.
Existing demo rows and all user edits are preserved on subsequent runs.
"""
import hashlib
import json
import os
import subprocess
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from start import HERE, ROOT, STATE, CONTAINER, OWNER, PORTABLE

os.environ.clear()
os.environ.update({
    'PATH': '/usr/bin:/bin', 'HOME': str(STATE / 'home'),
    'TMPDIR': str(STATE / 'temp'), 'LANG': 'C.UTF-8',
    'DJANGO_SETTINGS_MODULE': 'manual_settings', 'DJANGO_TESTING': '1',
    'DJANGO_DEBUG': '1', 'DJANGO_SECRET_KEY': 'local-synthetic-manual-preview-only',
    'DATABASE_URL': '', 'LEGACY_DATABASE_URL': '', 'REDIS_URL': '',
    'GOOGLE_APPLICATION_CREDENTIALS': '', 'TASK33_QA_ROOT': str(STATE),
    'TASK33_QA_SOCKET': str(STATE / 'socket'), 'TASK33_QA_OUTPUT': str(STATE),
    'PYTHONDONTWRITEBYTECODE': '1',
})
sys.path[:0] = [str(HERE), str(ROOT / 'docs/task33/qa04'), str(ROOT / 'src')]
os.chdir(ROOT)

info = json.loads(subprocess.check_output(['docker', 'inspect', CONTAINER]))[0]
assert info['Config']['Labels'].get('kidsmap.manual.owner') == OWNER
assert info['HostConfig']['NetworkMode'] == 'none'
assert not info['HostConfig']['PortBindings']

import django
from django.conf import settings
from guard import validate_settings, install_network_guard, install_libpq_guard

validate_settings(settings)
install_network_guard()
install_libpq_guard()
django.setup()

from django.contrib.auth import get_user_model
from django.core.files import File
from django.db import transaction
from django.utils import translation
from catalog.models import Place, PlacePhoto, Category, Subcategory, Activity, OfferingGroup, PricingPlan
from catalog.management.commands.seed_catalog_demo_places import Command
from catalog.services.content_quality import public_place_queryset
from catalog.services.district_geometry import resolve_location
from catalog.testcases.utils import create_ready_place

MARKER = 'seed:manual-demo100-20261004:'
OUT = STATE / 'demo100' if PORTABLE else HERE.parent / 'demo100'
CATEGORY_NAMES = {
    'ART': ('Творчество', 'Yaradıcılıq', 'Arts'),
    'CAMP': ('Лагеря', 'Düşərgələr', 'Camps'),
    'EDU': ('Образование', 'Təhsil', 'Education'),
    'FUN': ('Развлечения', 'Əyləncə', 'Entertainment'),
    'MUS': ('Музыка', 'Musiqi', 'Music'),
    'PARK': ('Парки', 'Parklar', 'Parks'),
    'SPRT': ('Спорт', 'İdman', 'Sports'),
    'TECH': ('Технологии', 'Texnologiya', 'Technology'),
    'WATERPARK': ('Аквапарки', 'Akvaparklar', 'Water parks'),
    'dance': ('Танцы', 'Rəqs', 'Dance'),
    'intellect-skills': ('Развитие навыков', 'Bacarıqların inkişafı', 'Skills development'),
}


def digest(rows):
    return hashlib.sha256(json.dumps(list(rows), sort_keys=True, default=str).encode()).hexdigest()


def main():
    templates = Command()._build_templates()
    sources = {p for t in templates for p in (t.photo_path, t.cover_photo_path, *t.gallery_photo_paths)}
    assert all((ROOT / p).is_file() for p in sources)
    existing = Place.objects.filter(additional_info__startswith=MARKER)
    inspection = {'total_before': Place.objects.count(), 'batch_already_present': existing.count(),
                  'templates': len(templates), 'source_photos': len(sources),
                  'categories': sorted({t.category for t in templates})}
    print(json.dumps(inspection), flush=True)
    if '--apply' not in sys.argv:
        return
    OUT.mkdir(exist_ok=True)
    prior_rows = list(Place.objects.order_by('pk').values())
    prior_ids = [r['id'] for r in prior_rows]
    before_hash = digest(prior_rows)
    stamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%SZ')
    backup_dir = STATE / 'backups'
    backup_dir.mkdir(exist_ok=True)
    backup = backup_dir / f'before-demo100-{stamp}.dump'
    with backup.open('xb') as stream:
        subprocess.run(['docker', 'exec', CONTAINER, 'pg_dump', '-h', '/qa-socket',
                        '-U', 'qa_stage04', '-d', 'qa_stage04', '-Fc'], stdout=stream, check=True)
    owner = get_user_model().objects.get(username='demo_owner')
    created = []
    with transaction.atomic():
        # Serialise concurrent invocations of this seed only.
        from django.db import connection
        with connection.cursor() as cursor:
            cursor.execute('SELECT pg_advisory_xact_lock(%s)', [20261004100])
        for index in range(1, 101):
            marker = f'{MARKER}{index:03d}'
            if Place.objects.filter(additional_info=marker).exists():
                continue
            t = templates[(index - 1) % len(templates)]
            cycle = (index - 1) // len(templates)
            ru, az, en = CATEGORY_NAMES[t.category]
            category, _ = Category.objects.get_or_create(code=t.category,
                defaults={'name': ru, 'name_ru': ru, 'name_az': az, 'name_en': en, 'is_active': True})
            subcategory, _ = Subcategory.objects.get_or_create(code='demo100-' + t.subcategory[:40],
                defaults={'category': category, 'name': t.name_ru,
                          'name_ru': t.name_ru, 'name_az': t.name_az, 'name_en': t.name_en})
            assert subcategory.category_id == category.pk
            price = max(10, t.price_from) + cycle * 5
            lat, lng = t.lat + cycle * .0008, t.lng + cycle * .0006
            if resolve_location(lat, lng).status != 'resolved':
                lat, lng = 40.40 + index * .00001, 49.82 + index * .00001
            location = resolve_location(lat, lng)
            assert location.status == 'resolved'
            p = create_ready_place(with_pricing_plan=False,
                owner=owner, created_by=owner, slug=f'manual-demo100-{index:03d}',
                name=f'Демо · {t.name_ru} {index:03d}', name_ru=f'Демо · {t.name_ru} {index:03d}',
                name_az=f'Demo · {t.name_az} {index:03d}', name_en=f'Demo · {t.name_en} {index:03d}',
                description_ru=t.description_ru + ' Это вымышленное место для локальной проверки KidsMap. Фотографии иллюстративные. Можно проверить возрастные группы, расписание и стоимость занятия.',
                description_az=t.description_az + ' Bu, KidsMap yerli yoxlaması üçün uydurma məkandır. Şəkillər nümunədir. Yaş qrupları, dərs cədvəli və qiymətlər sınaq üçün təqdim olunur.',
                description_en=t.description_en + ' This fictional place is for local KidsMap testing. Photos are illustrative. Explore the sample age groups, timetable and lesson prices; no real bookings are available.',
                category=category, subcategory=subcategory, district=location.district_key, metro='',
                address=f'Bakı — demo ünvan / тестовый адрес {index:03d}',
                phone1='', website='https://example.invalid/kidsmap-demo', instagram='',
                age_from=t.age_from, age_to=t.age_to, price_from=price, price_to=price,
                lat=lat, lng=lng,
                photo='', schedule='Mon–Fri 09:00–18:00; Sat 10:00–16:00',
                lesson_duration_minutes=t.lesson_duration_minutes, additional_info=marker,
                additional_info_ru='Демонстрационные данные, не реальное заведение.',
                additional_info_az='Nümayiş məlumatları, real məkan deyil.',
                additional_info_en='Demo data, not an actual venue.',
                published_at=django.utils.timezone.now())
            for field, source in [('photo', t.photo_path), ('cover_photo', t.cover_photo_path)]:
                with (ROOT / source).open('rb') as stream:
                    getattr(p, field).save(f'manual-demo100-{index:03d}-{field}{Path(source).suffix}', File(stream), save=False)
            p.save(update_fields=['photo', 'cover_photo'])
            gallery_sources = list(dict.fromkeys(t.gallery_photo_paths))[:2]
            for order, source in enumerate(gallery_sources, 1):
                photo = PlacePhoto(place=p, order=order, caption=f'Demo {index:03d} · {order}')
                with (ROOT / source).open('rb') as stream:
                    photo.image.save(f'manual-demo100-{index:03d}-gallery-{order}{Path(source).suffix}', File(stream), save=False)
                photo.save()
            a = Activity.objects.create(place=p, category=category, subcategory=subcategory,
                name_ru=f'{t.name_ru} — занятие', name_az=t.name_az, name_en=t.name_en, status='published')
            group = OfferingGroup.objects.create(activity=a, name_ru='Основная группа',
                name_az='Əsas qrup', name_en='Main group', age_from=t.age_from, age_to=t.age_to,
                lesson_format='group', language=('az', 'ru', 'en')[(index - 1) % 3],
                schedule_text='Saturday 10:00–11:00')
            PricingPlan.objects.create(offering_group=group, product_type='lesson',
                price_kind='exact', price=price, is_active=True)
            created.append(p.pk)
        assert digest(Place.objects.filter(pk__in=prior_ids).order_by('pk').values()) == before_hash
        assert Place.objects.filter(additional_info__startswith=MARKER).count() == 100
        assert public_place_queryset(Place.objects.filter(additional_info__startswith=MARKER)).count() == 100
    batch = list(Place.objects.filter(additional_info__startswith=MARKER).order_by('pk'))
    files = [f for p in batch for f in [p.photo, p.cover_photo, *[g.image for g in p.gallery.all()]]]
    assert all(f.storage.exists(f.name) and f.size > 0 for f in files)
    with translation.override('ru'):
        urls = [p.get_absolute_url() for p in batch]
    result = dict(inspection, created=len(created), total_after=Place.objects.count(),
        public_batch=100, public_total=public_place_queryset(Place.objects.all()).count(),
        existing_places_unchanged=True, existing_places_sha256=before_hash,
        photos_verified=len(files), activities=Activity.objects.filter(place__in=batch).count(),
        groups=OfferingGroup.objects.filter(activity__place__in=batch).count(),
        categories=dict(Counter(p.category_id for p in batch)),
        districts=dict(Counter(p.district for p in batch)),
        backup=str(backup), created_ids=created, urls=urls)
    result_file = OUT / ('results.json' if not (OUT / 'results.json').exists() else f'verification-{stamp}.json')
    result_file.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({k: v for k, v in result.items() if k not in ('created_ids', 'urls')}, ensure_ascii=False))


if __name__ == '__main__':
    main()
