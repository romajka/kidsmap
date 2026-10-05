"""One-shot, explicit baseline-contract fixture updates (not a runtime test hook)."""
from pathlib import Path

p = Path('src/catalog/testcases/public.py')
s = p.read_text(encoding='utf-8')
def replace(old, new, count=1):
    global s
    assert old in s, old
    s = s.replace(old, new, count)

replace('<strong>{{ map_places|length }}</strong>', '<strong>{{ map_business_count }}</strong>')
replace('{{ map_places|length }}+</strong>', '{{ map_business_count }}+</strong>')
replace('district="Тестовый район",\n        )', 'district="Тестовый район", lat=None, lng=None,\n        )')
for district in ('Забрат','Ахмедлы','Бинагади'):
    replace(f'district="{district}", metro=', f'district="{district}", lat=None, lng=None, metro=')
replace('district="Ясамал",\n        )\n        partial_place', 'district="Ясамал", lat=None, lng=None,\n        )\n        partial_place')
replace('district="Новый Ясамал",\n        )', 'district="Новый Ясамал", lat=None, lng=None,\n        )')
replace('district="agdash",\n        )', 'district="agdash", lat=None, lng=None,\n        )')
# Stable fixtures must describe the district of their point. Use an address-only
# card where the test concerns a manual district, not point-based normalization.
replace('name="Seo Place",\n            name_ru="SEO кружок",', 'name="Seo Place",\n            name_ru="SEO кружок", lat=None, lng=None,')
replace('name="Sitemap place",\n            name_ru="Место для sitemap",', 'name="Sitemap place",\n            name_ru="Место для sitemap",\n            name_en="Sitemap place", description_ru="Занятия для детей с опытными педагогами.",\n            description_en="Classes for children led by experienced teachers.",')
replace('self.assertNotIn(out_of_range_place.name_ru, names)', 'self.assertIn(out_of_range_place.name_ru, names)\n        # Budget filtering was removed: a legacy URL must not silently hide cards.\n        self.assertNotContains(response, \'name="price_from"\')\n        self.assertNotContains(response, \'name="price_to"\')')
replace('self.assertFalse(place_review.is_anonymous)', 'self.assertTrue(place_review.is_anonymous)')
replace('self.assertEqual(place_review.author_name_i18n, "Мария")', 'with override("ru"):\n            self.assertEqual(place_review.author_name_i18n, "Аноним")\n        self.assertEqual(place_review.author_name, "Мария")')
replace('Kateqoriya, rayon, yaş və büdcə bir yerdə.', 'Kateqoriya, rayon və yaş bir yerdə.')
replace('self.assertNotContains(response, \'name="q"\')\n        self.assertNotContains(response, \'name="category"\')', 'self.assertContains(response, \'name="q"\')\n        self.assertContains(response, \'name="category"\')')
replace('self.assertNotContains(response, \'name="district"\')\n        self.assertNotContains(response, \'name="age_from"\')', 'self.assertContains(response, \'name="district"\')\n        self.assertContains(response, \'name="period"\')\n        self.assertNotContains(response, \'name="age_from"\')')
# Public location is the approved venue snapshot, not a mutable legacy address.
for address in ('ул. Школьная 9, Баку', 'пр. Гусейна Джавида 18, Баку'):
    replace(f'self.upcoming_event.address = "{address}"\n        self.upcoming_event.save(update_fields=["address", "updated_at"])',
        f'self.upcoming_event.venue_snapshot = {{"address": "{address}"}}\n        self.upcoming_event.address = "Legacy address must not leak"\n        self.upcoming_event.save(update_fields=["venue_snapshot", "address", "updated_at"])')
p.write_text(s, encoding='utf-8')
