#!/bin/sh
set -u
qa=/mnt/c/kidsmap/.tmp/social09-pc-fix-r1
docker exec m09s09-fix-r1-app python "$qa/runtime.py" test catalog.testcases.test_social_qa09_feed_query.SocialQA09FeedQueryTests catalog.testcases.public.TestPublicPagesSmoke.test_legacy_redirect_keeps_catalog_filter_but_drops_foreign_query catalog.testcases.public.TestReviewEnhancements.test_site_reviews_page_can_sort_reviews_by_likes catalog.testcases.test_organization_directory.OrganizationDirectoryTests.test_directory_seo_and_language_links_preserve_only_public_filters > "$qa/tests.log" 2>&1
result=$?
printf '%s\n' "$result" > "$qa/tests.exit"
tail -n 11 "$qa/tests.log"
exit "$result"
