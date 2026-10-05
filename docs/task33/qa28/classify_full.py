"""Preserve actual full-suite failures and classify accepted-contract fixture debt."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[3]
reports=root/'docs/task33/reports'
current=json.loads((reports/'28-full-results.json').read_text(encoding='utf8'))
old=json.loads((reports/'24-results.json').read_text(encoding='utf8'))['classification']['remaining_problem_entries']
by_id={r['id']:r for r in old}
new={
 'catalog.testcases.admin.TestAdminBulkActions.test_event_make_published_and_draft_action':
 ('EVENT_ORGANIZER_INTERVAL_CONTRACT','src/catalog/testcases/admin.py:TestAdminBulkActions.test_event_make_published_and_draft_action','src/catalog/services/event_domain.py:publish_event','Fixture publishes organizerless Event without exact interval; accepted organizer/publication checks reject it.'),
 'catalog.testcases.admin.TestAdminOwnershipModerationUX.test_event_admin_bulk_publish_action_updates_status':
 ('EVENT_ORGANIZER_INTERVAL_CONTRACT','src/catalog/testcases/admin.py:TestAdminOwnershipModerationUX.test_event_admin_bulk_publish_action_updates_status','src/catalog/services/event_domain.py:publish_event','Fixture has no organizer or interval; bulk publication correctly refuses it.'),
 'catalog.testcases.admin.TestAdminOwnershipModerationUX.test_event_admin_can_publish_from_change_form':
 ('EVENT_ADMIN_LEGACY_PAYLOAD','src/catalog/testcases/admin.py:TestAdminOwnershipModerationUX._admin_event_change_payload','src/catalog/domain_admin/place.py:EventAdminForm._post_clean','Old payload omits required event_format and organizer; current publication requires explicit organizer.'),
 'catalog.testcases.admin.TestAdminOwnershipModerationUX.test_event_admin_can_save_draft_and_continue_later':
 ('EVENT_ADMIN_LEGACY_PAYLOAD','src/catalog/testcases/admin.py:TestAdminOwnershipModerationUX._admin_event_change_payload','src/catalog/domain_admin/place.py:EventAdmin.get_fieldsets','After verified precision fix, original payload still fails solely missing event_format; complete payload302/draft proven by28-legacy-draft-diagnostic.json, with original assertion retained.'),
 'catalog.testcases.public.EventsLandingTests.test_event_address_is_localized_for_az_public_pages':
 ('EVENT_IMMUTABLE_SNAPSHOT','src/catalog/testcases/public.py:EventsLandingTests.test_event_address_is_localized_for_az_public_pages','src/catalog/templates/catalog/includes/event_listing_card.html','Test mutates legacy address after the approved venue snapshot; current cards read immutable venue_snapshot.'),
 'catalog.testcases.public.EventsLandingTests.test_event_address_is_localized_for_en_public_pages':
 ('EVENT_IMMUTABLE_SNAPSHOT','src/catalog/testcases/public.py:EventsLandingTests.test_event_address_is_localized_for_en_public_pages','src/catalog/templates/catalog/includes/event_listing_card.html','Test mutates legacy address after the approved venue snapshot; accepted historical venue must stay unchanged.'),
 'catalog.testcases.public.EventsLandingTests.test_events_landing_does_not_render_filter_controls':
 ('EVENT_CALENDAR_FILTER_CONTRACT','src/catalog/testcases/public.py:EventsLandingTests.test_events_landing_does_not_render_filter_controls','src/catalog/templates/catalog/events_landing.html','Assertion bans q/category/age controls explicitly required by accepted stage27 list/calendar filtering.'),
 'catalog.testcases.public.TestPublicPagesSmoke.test_sitemap_lastmod_matches_model_updated_at':
 ('SITEMAP_ACTIVE_TIMEZONE_EXPECTATION','src/catalog/testcases/public.py:TestPublicPagesSmoke.test_sitemap_lastmod_matches_model_updated_at','src/catalog/sitemaps.py:PlaceSitemap.lastmod','Unchanged test compares UTC strftime date against sitemap XML date localized to Asia/Baku. UTC20:00–23:59 crosses local midnight; deterministic original-assertion UTC/Baku replay and independent retained-V2 SHA/source review prove time-dependent expectation debt.'),
}
entries=[]
for problem in current['suite-results.json']['problems']:
    row=dict(problem)
    if row['id']in by_id:
        original=by_id[row['id']]
        assert (row['kind'],row['exception'])==(original['kind'],original['exception'])
        row['classification']=original['classification']
        row['evidence']='24-results.json:classification.remaining_problem_entries; current retained ID/kind/exception; unchanged accepted decisions'
    else:
        category,fixture,source,reason=new[row['id']]
        row.update(classification=category,fixture_source=fixture,contract_source=source,reason=reason,
                   independent_review='28-sitemap-independent-classification.json'if category=='SITEMAP_ACTIVE_TIMEZONE_EXPECTATION'else'28-full-independent-classification.json')
    entries.append(row)
assert len(set(new))==8 and len(entries)==120
current['classification']={'status':'CLASSIFIED_NOT_GREEN','current_entries':len(entries),
 'current_unique_ids':len({r['id']for r in entries}),'retained_unique_ids':101,
 'new_contract_fixture_ids':7,'additional_time_dependent_expectation_ids':1,'unknown_ids':[],
 'note':'Failures remain in unchanged assertions. Accepted current contracts pass580 Task33 cases; this does not turn the full suite green. Additional sitemap date expectation occurs only across UTC/Baku day boundary.',
 'remaining_problem_entries':entries}
(reports/'28-full-results.json').write_text(json.dumps(current,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print(json.dumps({'entries':len(entries),'unique':len({r['id']for r in entries}),'unknown':0,'full_status':'NOT_GREEN'}))
