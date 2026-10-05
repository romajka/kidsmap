"""Replay the legacy name-audit scenario through the approved publication protocol."""
import ast
from pathlib import Path
ROOT=Path(__file__).resolve().parents[4];path=ROOT/'src/catalog/testcases/owner.py'
source=path.read_text();node=next(n for n in ast.walk(ast.parse(source)) if isinstance(n,ast.FunctionDef) and n.name=='test_owner_edit_creates_place_change_audit')
body='''    def test_owner_edit_creates_place_change_audit(self):
        # Task33 stores moderation provenance in the versioned candidate.
        self.place = create_ready_place(owner=self.owner_manager, name_ru="Кружок команды",
                                        district="baku_yasamal", lat=None, lng=None)
        self.client.login(username="team_owner_manager", password="StrongPass123!!")
        url = reverse("owner_place_edit", args=[self.place.id])
        rendered = self.client.get(url)
        self.assertEqual(rendered.status_code, 200)
        form = rendered.context['form']
        data = {name: form[name].value() for name in form.fields if form[name].value() is not None}
        data.update(name_ru="Кружок команды обновлен", form_action="save_and_publish")
        response = self.client.post(url, data=data, follow=True)
        self.assertEqual(response.status_code, 200)
        self.place.refresh_from_db()
        self.assertEqual(self.place.name_ru, "Кружок команды")
        revision = VolunteerPlaceRevision.objects.get(place=self.place)
        self.assertEqual(revision.status, 'pending')
        self.assertEqual(revision.author_id, self.owner_manager.pk)
        self.assertEqual(revision.schema_version, 1)
        self.assertEqual(revision.base_content_version, self.place.content_version)
        self.assertEqual(revision.base_snapshot['name_ru'], "Кружок команды")
        self.assertIn('name_ru', revision.changed_fields)
        self.assertEqual(revision.payload['name_ru'], "Кружок команды обновлен")
        from catalog.services import publication
        reviewer = User.objects.create_superuser('owner_audit_reviewer', password='password')
        publication.review(actor=reviewer, revision_id=revision.pk, version=revision.version, approve=True)
        self.place.refresh_from_db(); revision.refresh_from_db()
        self.assertEqual(self.place.name_ru, "Кружок команды обновлен")
        self.assertEqual(revision.status, 'approved')
        self.assertEqual(revision.reviewed_by_id, reviewer.pk)
'''
lines=source.splitlines(keepends=True);lines[node.lineno-1:node.end_lineno]=[body]
path.write_text(''.join(lines))
print('Name candidate/approved provenance scenario retained and replayed with actual GET/POST token.')
