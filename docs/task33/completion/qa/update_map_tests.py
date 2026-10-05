from pathlib import Path
p=Path('src/catalog/testcases/public.py')
s=p.read_text(encoding='utf-8')
start=s.index('    def test_catalog_map_uses_only_filtered_map_ready_places')
end=s.index('    def test_az_place_detail_uses_translated_labels_and_duration',start)
part=s[start:end].replace('lat=40.3771,','lat=40.4,').replace('lng=49.8412,','lng=49.8,')
for actual, obj in [('response.context["catalog_map_places"]','matching_place'),('serialized','place')]:
    old='        self.assertEqual(\n            '+actual+',\n            [\n'
    assert old in part
    part=part.replace(old,'        expected = [\n',1)
    boundary=part.index('            ],\n        )',part.index('        expected = ['))
    extra=f'''            ]
        member = expected[0]
        member.update(district={obj}.district, district_label={obj}.district_i18n({"language_code" if obj=="matching_place" else "'ru'"}),
            metro={obj}.metro, metro_label={obj}.metro_i18n({"language_code" if obj=="matching_place" else "'ru'"}),
            matched_offers=[], translation_fallback=False,
            content_language={"language_code" if obj=="matching_place" else "'ru'"}, translation_label='')
        expected = [{{**member, 'key': f'place:{{{obj}.pk}}', 'members': [member]}}]
        self.assertEqual({actual}, expected)'''
    part=part[:boundary]+extra+part[boundary+len('            ],\n        )'):]
s=s[:start]+part+s[end:]
s=s.replace('self.assertIn("дзюдо", response.context["map_places"][0]["search_text"])', '''# Map search now uses the shared server endpoint, including subcategory filters.
        point = response.context["map_places"][0]
        filtered = self.client.get(reverse('public_map'), {'category': category.pk, 'subcategory': subcategory.pk})
        self.assertEqual(filtered.status_code, 200)
        self.assertEqual([p['id'] for p in filtered.json()['points']], [point['id']])
        self.assertEqual(filtered.json()['points'][0]['members'][0]['id'], point['id'])
        wrong = self.client.get(reverse('public_map'), {'category': 'EDU'})
        self.assertEqual(wrong.json()['points'], [])''')
for name in ['Counted One','Education One']:
    s=s.replace(f'name="{name}",', f'name="{name}", lat=None, lng=None,',1)
p.write_text(s,encoding='utf-8')
