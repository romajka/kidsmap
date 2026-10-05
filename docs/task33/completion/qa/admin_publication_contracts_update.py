import ast
from pathlib import Path
path=Path(__file__).resolve().parents[4]/'src/catalog/testcases/admin.py'
source=path.read_text(encoding='utf-8')
tree=ast.parse(source)
n=next(n for n in ast.walk(tree) if isinstance(n,ast.FunctionDef) and n.name=='test_failed_publish_keeps_published_card_active_and_shows_all_issues')
lines=source.splitlines(keepends=True)
body='''    def test_failed_publish_keeps_published_card_active_and_shows_all_issues(self):
        self.place = create_ready_place(name='Approved card', name_ru='Одобренная карточка')
        before = (self.place.name_az, self.place.description_az, self.place.content_version)
        payload = self._admin_place_change_payload(_publish_place='1', name_az='', description_az='')
        response = self.client.post(reverse('admin:catalog_place_change', args=[self.place.pk]), payload)
        self.assertEqual(response.status_code, 200)
        form = response.context['adminform'].form
        self.assertIn('name_az', form.errors)
        self.assertIn('description_az', form.errors)
        for field in ('name_az', 'description_az'):
            for error in form.errors[field]:
                self.assertContains(response, escape(error))
        self.place.refresh_from_db()
        self.assertEqual(self.place.status, 'published'); self.assertTrue(self.place.is_active)
        self.assertEqual((self.place.name_az,self.place.description_az,self.place.content_version), before)
        from catalog.models import VolunteerPlaceRevision
        self.assertFalse(VolunteerPlaceRevision.objects.filter(place=self.place).exists())
'''
source=''.join(lines[:n.lineno-1])+body+''.join(lines[n.end_lineno:])
# Actual readiness, without a mocked readiness result or empty tariff replacement.
n=next(n for n in ast.walk(ast.parse(source)) if isinstance(n,ast.FunctionDef) and n.name=='test_place_admin_can_publish_ready_place_from_change_form')
lines=source.splitlines(keepends=True); text=''.join(lines[n.lineno-1:n.end_lineno])
start=text.index('        with patch("catalog.domain_admin.place.place_quality_check")')
end=text.index('        if response.context',start)
text=text[:start]+'''        payload['pricing_plans'] = json.dumps(ready_place.pricing_plans)
        response = self.client.post(reverse('admin:catalog_place_change', args=[ready_place.pk]), payload)

'''+text[end:]
text=text.replace('self.assertTrue(ready_place.is_active)', 'self.assertTrue(ready_place.is_active, [str(m) for m in response.wsgi_request._messages])')
source=''.join(lines[:n.lineno-1])+text+''.join(lines[n.end_lineno:])
ast.parse(source);path.write_text(source,encoding='utf-8')
print('Publication form contract scenarios updated')
