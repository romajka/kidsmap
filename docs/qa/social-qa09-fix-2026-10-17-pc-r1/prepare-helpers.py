from pathlib import Path
Q=Path(__file__).resolve().parent
p=Q/'cell-body.js';t=p.read_text();t=t.replace("fits.push(await fit());\n await page.locator('.pagination').scrollIntoViewIfNeeded();", "fits.push(await fit());\n const p2Reload=await page.reload();await finite();const reload2=p2Reload.status()===200&&page.url()===p2.url&&await active()===p2.active&&JSON.stringify(await texts('place'))===JSON.stringify(p2.texts);\n await page.locator('.pagination').scrollIntoViewIfNeeded();",1)
t=t.replace("fits.push(await fit());\n const form=", "fits.push(await fit());\n const p3Reload=await page.reload();await finite();const reload3=p3Reload.status()===200&&page.url()===p3.url&&await active()===p3.active&&JSON.stringify(await texts('place'))===JSON.stringify(p3.texts);\n const form=",1)
t=t.replace("fits.push(await fit());\n await page.locator('.place-reviews-toolbar-wrap')", "fits.push(await fit());\n const likesReload=await page.reload();await finite();const reloadLikes=likesReload.status()===200&&page.url()===likes.url&&await page.locator('select[name=\"sort\"]').inputValue()==='likes'&&JSON.stringify(await texts('place'))===JSON.stringify(likes.texts);\n await page.locator('.place-reviews-toolbar-wrap')",1)
t=t.replace(' const source={',' controls.reload_page2=reload2;controls.reload_page3=reload3;controls.reload_likes=reloadLikes;\n const source={')
p.write_text(t)
p=Q/'matrix.py';t=p.read_text().replace("assert all(row['controls'].values()),row['controls']", "assert all(row['controls'].values()) and all(row['source'].values()),(row['controls'],row['source'])");p.write_text(t)
p=Q/'run-seo-probes.py';t=p.read_text().replace("all(r['controls'].values())", "all(r['controls'].values()) and all(r['source'].values())");p.write_text(t)
(Q/'tests.sh').write_text('''#!/bin/sh
set -u
qa=/mnt/c/kidsmap/.tmp/social09-pc-fix-r1
docker exec m09s09-fix-r1-app python "$qa/runtime.py" test catalog.testcases.test_social_qa09_feed_query.SocialQA09FeedQueryTests catalog.testcases.public.TestPublicPagesSmoke.test_legacy_redirect_keeps_catalog_filter_but_drops_foreign_query catalog.testcases.public.TestReviewEnhancements.test_site_reviews_page_can_sort_reviews_by_likes catalog.testcases.test_organization_directory.OrganizationDirectoryTests.test_directory_seo_and_language_links_preserve_only_public_filters > "$qa/tests.log" 2>&1
result=$?
printf '%s\\n' "$result" > "$qa/tests.exit"
tail -n 11 "$qa/tests.log"
exit "$result"
''')
(Q/'run_json.py').write_text((Q.parent/'social08-pc-fix-r1/run_json.py').read_text())
print('Original15controls/6source assertions retained;3reload controls added;12targeted method labels prepared')
