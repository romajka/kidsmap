# SITE20 — разрешённые действия редакторов: Implementation Plan

> **For agentic workers:** Execute inline task-by-task under the repository engineering contract. The approved scope is binding; no delegation or commits are requested.

**Goal:** В режиме просмотра убрать недоступное сохранение и пустую карточку действий; сохранить разрешённые сохранение, добавление и удаление.

**Architecture:** Использовать переданные Django `has_change_permission`, `has_add_permission`, `has_delete_permission` и `add` в общем шаблоне девяти редакторов. Save и editable marker разрешены при change либо add+add permission. Блок действий присутствует при разрешённом сохранении или существующем разрешённом delete. Серверная авторизация остаётся источником прав.

**Tech Stack:** installed Django 6.0.2, Jazzmin, Django templates, existing scoped CSS, PostgreSQL, Chromium1247 through Playwright CLI.

**Spec:** [Current finding and evidence](REPORT.md), [original SITE20](../site-qa19-fix-2026-10-18-pc-r1/findings/SITE-QA-20.md).

## Global Constraints

- LOCAL HEAD852938d96764ae315b92859e3651e5ea62054a36; branch codex/module09-transfer-2026-10-16-r1; dirty WORKTREE1034sources preserved. Production UNKNOWN.
- Status PLAN READY / NOT APPLIED. Human «дальше» authorizes this investigation/plan; application implementation awaits this separate scope decision under AGENTS.md. Earlier SITE22 approval covered only SITE22.
- Scope exactly2files in candidate-manifest.json. No CSS/JS/PO/model/schema/ACL/preset/revision/destination/public behavior edits. No commit/push/deploy/production/cleanup; no new module11.
- Tests DJANGO_TESTING=1 before setup, env cleared, own DB/cache/media/email, current three isolated locales, integrations disabled, read-only repository except explicit approved application patch.
- All source/QA packages/MO/.cbmignore/refs/index bytes/foreign runtimes preserved. Guide and MASTER append-only. No raw private records/secrets/logs/graph caches in artifacts.

### Task 1: Action visibility in the existing shared settings template

**Files:** Modify `src/catalog/templates/admin/catalog/shared_settings_change_form.html`; create `src/catalog/testcases/test_site_qa20_permission_actions.py`.

**Interfaces:** existing Django change-form context. Exact predicate for saves and editable marker: `has_change_permission or add and has_add_permission`; delete keeps `has_delete_permission and not add`. Nine consumers: six SiteSettings section proxies, SiteAnalytics, CatalogContentSettings, SiteGalleryImage. Add-only gallery must gain existing mobile editable styling; delete-only plus view retains its existing delete link and gains no save controls.

- [ ] Revalidate all before/candidate hashes and diff SHA from candidate-manifest; confirm unchanged snapshot/prior closure evidence.
- [ ] Prepare a fresh own profile `m10s20-fix-r1-app`, loopback33630, normal DB `m10s20_fix_r1`, RED `test_m10s20_fix_r1`, own separate media/cache/private-media/email. Build current isolated AZ/RU/EN locales before setup. Reuse isolated configuration patterns in this package, without executing scripts in any sealed prior package.
- [ ] Copy the complete candidate regression below into own scratch module `test_site20_candidate`; fresh RED command: `docker exec m10s20-fix-r1-app python /mnt/c/kidsmap/.tmp/site20-pc-fix-r1/runtime.py test test_site20_candidate`. Expect8methods,3failed methods/29failure observations,0errors on this source snapshot. Current PLAN evidence proves this RED; do not claim fresh fix-profile RED until executed.
- [ ] Apply exactly proposed.diff after user scope approval; preserve CRLF and unrelated bytes. New test bytes must equal candidate hash. No test expectation changes to obtain GREEN.
- [ ] Run fresh GREEN with new disposable `test_m10s20_fix_green_r1`, same isolation and runtime test command using these labels: `catalog.testcases.test_site_qa20_permission_actions catalog.testcases.test_site_qa22_save_exit catalog.testcases.test_site_qa19_catalog_content catalog.testcases.public.TestCatalogContentSettingsWiring catalog.testcases.test_site_qa06_media_validation catalog.testcases.test_site_qa01_media_permissions catalog.testcases.test_site_qa15_settings_concurrency catalog.testcases.admin.TestSiteGalleryImageAdminMedia catalog.testcases.admin.TestAdminSidebarStructure catalog.testcases.test_public_section_switches`. Expected122unique methods (114existing+8new), no failures/errors. No GREEN run or application behavior claim in PLAN.
- [ ] Actual-source native browser acceptance after apply: all9consumers, viewer/change-only, AZ/RU/EN at360/390/768/1024/1280/1440; add-only gallery GET+valid native add/error/retry/both save actions, view+delete gallery link retained, denied users and forged viewer POST403 with row/log/media no-write. Test keyboard Tab/Enter has no unavailable save targets; allowed actions retain focus/labels. Check no overflow, current CSSHTTP200, no unexpected console/pageerrors/localHTTP. No injected classes/styles/transport rewrite in acceptance.
- [ ] Preserve SITE22 one-hop hub exits for six sections and `_continue` editor behavior, SITE15 invalid/stale no-write, SITE06 media validation, SITE19 JSON saves/errors, SITE08 responsive layout. Place/Event neighbor form controls/geometry must remain unchanged. Observe existing mobile delete visibility separately; do not claim a redesign of delete-only mobile controls.
- [ ] Verify exact original/scoped fixtures or explicitly qualified form normalization/cache derivatives; retain synthetic logs/timestamps. Report all failures, recovery and NOT RUN. Preserve prior packages; append guide/MASTER; seal artifacts. Only then consider scoped SITE20 CLOSED LOCAL; full module10 acceptance remains separate.

## Exact reviewable patch

```diff
--- a/src/catalog/templates/admin/catalog/shared_settings_change_form.html
+++ b/src/catalog/templates/admin/catalog/shared_settings_change_form.html
@@ -13,7 +13,7 @@
 {% block submit_buttons_bottom %}{% endblock %}
 
 {% block content %}
-  <div id="content-main" class="km-place-form-page km-settings-form-page col-12{% if has_change_permission %} km-settings-form-page--editable{% endif %}">
+  <div id="content-main" class="km-place-form-page km-settings-form-page col-12{% if has_change_permission or add and has_add_permission %} km-settings-form-page--editable{% endif %}">
     <form
       {% if has_file_field %}enctype="multipart/form-data"{% endif %}
       {% if form_url %}action="{{ form_url }}"{% endif %}
@@ -123,9 +123,11 @@
             {% endblock %}
           </main>
 
+          {% if has_change_permission or add and has_add_permission or has_delete_permission and not add %}
           <aside class="km-place-form-sidebar">
             <div class="km-place-sidebar-card km-place-sidebar-card--actions">
               <div class="km-place-sidebar-action-buttons">
+                {% if has_change_permission or add and has_add_permission %}
                 <!-- Группа 1: Основное действие -->
                 <div class="km-sidebar-action-group km-sidebar-action-group--primary">
                   <button type="submit" name="_continue" class="km-btn--sidebar km-btn--primary-save">
@@ -140,6 +142,7 @@
                   </button>
                 </div>
 
+                {% endif %}
                 <!-- Группа 3: Опасные действия -->
                 {% if has_delete_permission and not add %}
                   <div class="km-sidebar-action-group km-sidebar-action-group--danger">
@@ -151,6 +154,7 @@
               </div>
             </div>
           </aside>
+          {% endif %}
         </div>
       </div>
     </form>
--- /dev/null
+++ b/src/catalog/testcases/test_site_qa20_permission_actions.py
@@ -0,0 +1,116 @@
+"""SITE20: visible actions follow existing Django object/add permissions.
+
+Exercises real registered admin consumers; direct POST denial must remain intact.
+"""
+import tempfile
+from pathlib import Path
+from django.conf import settings
+from django.contrib.admin.models import LogEntry
+from django.contrib.auth import get_user_model
+from django.contrib.auth.models import Permission
+from django.test import TestCase, override_settings
+from django.urls import reverse
+from catalog.models import SiteSettings, CatalogContentSettings, SiteGalleryImage
+from catalog.models.site import clear_singleton_caches
+
+SECTIONS=('sitebrandingsettings','siteaboutsettings','sitecontactssettings',
+          'sitefootersettings','siteemptystatesettings','sitevisibilitysettings')
+MODELS=SECTIONS+('siteanalytics','catalogcontentsettings','sitegalleryimage')
+
+class Site20PermissionActionsTests(TestCase):
+    def setUp(self):
+        self.assertTrue(settings.TESTING)
+        self.temp=tempfile.TemporaryDirectory(prefix='site20-')
+        self.addCleanup(self.temp.cleanup)
+        storage=override_settings(MEDIA_ROOT=self.temp.name)
+        storage.enable();self.addCleanup(storage.disable)
+        clear_singleton_caches()
+        self.site=SiteSettings.get_solo();self.catalog=CatalogContentSettings.get_solo()
+        self.gallery=SiteGalleryImage.objects.create(image='fictional-site20.png',title_ru='Fictional SITE20')
+
+    def actor(self, name, grants):
+        user=get_user_model().objects.create_user('site20_'+name,name+'@example.invalid','fictional',is_staff=True)
+        permissions=Permission.objects.filter(content_type__app_label='catalog',codename__in=grants)
+        self.assertEqual(permissions.count(),len(grants));user.user_permissions.add(*permissions)
+        self.client.force_login(user)
+        return user
+
+    def url(self,model,add=False):
+        if add:return reverse('admin:catalog_'+model+'_add')
+        pk=self.gallery.pk if model=='sitegalleryimage' else self.catalog.pk if model=='catalogcontentsettings' else self.site.pk
+        return reverse('admin:catalog_'+model+'_change',args=[pk])
+
+    def snapshot(self):
+        return (list(SiteSettings.objects.values()),list(CatalogContentSettings.objects.values()),
+                list(SiteGalleryImage.objects.values()),LogEntry.objects.count(),
+                sorted(p.relative_to(self.temp.name).as_posix() for p in Path(self.temp.name).rglob('*') if p.is_file()))
+
+    def test_view_only_has_no_save_controls_or_empty_action_card(self):
+        self.actor('viewer',['view_'+m for m in MODELS])
+        before=self.snapshot()
+        for language in ('az','ru','en'):
+            self.client.cookies['django_language']=language
+            for model in MODELS:
+                with self.subTest(language=language,model=model):
+                    response=self.client.get(self.url(model));self.assertEqual(response.status_code,200)
+                    self.assertFalse(response.context['has_change_permission'])
+                    self.assertNotContains(response,'name="_save"')
+                    self.assertNotContains(response,'name="_continue"')
+                    self.assertNotContains(response,'km-place-sidebar-card--actions')
+        self.assertEqual(self.snapshot(),before)
+
+    def test_view_only_forged_posts_remain_forbidden_without_writes(self):
+        self.actor('postviewer',['view_'+m for m in MODELS]);before=self.snapshot()
+        for model in MODELS:
+            for action in ('_save','_continue'):
+                with self.subTest(model=model,action=action):
+                    self.assertEqual(self.client.post(self.url(model),{action:'1'}).status_code,403)
+        self.assertEqual(self.snapshot(),before)
+
+    def test_change_only_keeps_both_save_actions(self):
+        self.actor('editor',['change_'+m for m in MODELS])
+        for model in MODELS:
+            with self.subTest(model=model):
+                response=self.client.get(self.url(model));self.assertEqual(response.status_code,200)
+                self.assertContains(response,'name="_save"',count=1)
+                self.assertContains(response,'name="_continue"',count=1)
+                self.assertContains(response,'km-settings-form-page--editable')
+
+    def test_add_only_gallery_keeps_actions_and_editable_mobile_marker(self):
+        user=self.actor('adder',['add_sitegalleryimage'])
+        self.assertFalse(user.has_perm('catalog.change_sitegalleryimage'))
+        response=self.client.get(self.url('sitegalleryimage',add=True))
+        self.assertEqual(response.status_code,200);self.assertTrue(response.context['add'])
+        self.assertTrue(response.context['has_add_permission']);self.assertFalse(response.context['has_change_permission'])
+        self.assertContains(response,'name="_save"',count=1)
+        self.assertContains(response,'name="_continue"',count=1)
+        self.assertContains(response,'km-settings-form-page--editable')
+        self.assertNotContains(response,'deletelink')
+
+    def test_add_only_gallery_cannot_edit_existing_image(self):
+        self.actor('adderdenied',['add_sitegalleryimage']);before=self.snapshot()
+        self.assertEqual(self.client.get(self.url('sitegalleryimage')).status_code,403)
+        self.assertEqual(self.client.post(self.url('sitegalleryimage'),{'_save':'1'}).status_code,403)
+        self.assertEqual(self.snapshot(),before)
+
+    def test_view_and_delete_keeps_delete_without_offering_save(self):
+        self.actor('deleter',['view_sitegalleryimage','delete_sitegalleryimage'])
+        response=self.client.get(self.url('sitegalleryimage'));self.assertEqual(response.status_code,200)
+        self.assertContains(response,'deletelink',count=1)
+        self.assertNotContains(response,'name="_save"')
+        self.assertNotContains(response,'name="_continue"')
+
+    def test_singleton_add_routes_remain_forbidden(self):
+        self.actor('singletonadder',['add_'+m for m in MODELS]);before=self.snapshot()
+        for model in MODELS[:-1]:
+            with self.subTest(model=model):
+                self.assertEqual(self.client.get(self.url(model,add=True)).status_code,403)
+        self.assertEqual(self.snapshot(),before)
+
+    def test_denied_actor_cannot_read_or_post_any_consumer(self):
+        self.actor('denied',[]);before=self.snapshot()
+        for model in MODELS:
+            with self.subTest(model=model):
+                self.assertEqual(self.client.get(self.url(model)).status_code,403)
+                self.assertEqual(self.client.post(self.url(model),{'_continue':'1'}).status_code,403)
+        self.assertEqual(self.snapshot(),before)
```

## Evidence and risk

Current8method RED:3failed methods/29observations,5passed/0errors. Current actual-source75native rows:375controlsPASS/123expected action failures;3native viewer POST403/no writes. Candidate180isolated render/truth-table checks PASS, which prove template logic/compilation only. Candidate not applied; native candidate geometry, keyboard and add/save persistence still require approved implementation acceptance. Changed template is shared by9consumers; exact scope covers all their permission states. Existing deletion permission semantics remain Django's. Remaining SITE11 and other module10 findings stay open.
