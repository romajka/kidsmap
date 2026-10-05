import json
from pathlib import Path
root=Path(__file__).resolve().parents[4]
baseline=json.loads((root/'docs/task33/final-audit/domain-failure-classification.json').read_text(encoding='utf-8'))
modules={'catalog','image_uploads','photo_workflow','place_readiness','public','adult_classes'}
notes={
'test_map_serialization_query_count_does_not_grow_with_schedules': 'Application: fresh QuerySet is evaluated once, schedules once; unused gallery query removed and empty Activity query avoided through Exists. Original four-query assertion retained; new-structure scaling checked separately.',
'test_subcategory_combines_with_other_filters':'Correct Ganja address-only fixture; category+age represented by two real approved Activity/OfferingGroup pairs with own category/subcategory. Exact category, district and same-group age assertions retained.',
'test_card_changes_are_not_saved_when_gallery_storage_fails':'Valid signed source token reaches storage failure; unchanged name/gallery and concrete gallery_images error remain required.',
'test_main_photo_can_be_replaced_and_then_removed':'Signed owner edit → unchanged approved photo → candidate submission → real moderator approval → replacement/removal. Byte existence retained for the base_snapshot reference; public photo removal and new WebP bytes are checked.',
'test_gallery_can_be_added_and_owner_can_delete_a_photo':'Signed candidate upload, unchanged live gallery, real moderation, then owner deletion proposal and second real moderation. Deleted public row absent; referenced base_snapshot bytes retained.',
'test_gallery_order_is_persisted_and_foreign_ids_rejected':'Signed versioned photo endpoint; exact candidate order [oldB,new,oldA], durable upload and unchanged live order. Fresh token for foreign-ID rejection, candidate and live remain unchanged.',
'test_catalog_has_no_adult_filter_and_renders_compact_audience':'Current compact adult badge plus exact child ages and absence of adult filter asserted. No audience information removed.',
'test_place_detail_renders_children_only_and_mixed_audience':'Exact 6–17 age values in current fact markup; adult-group fact only on mixed card.',
'test_event_address_is_localized_for_az_public_pages':'Immutable approved venue fixture replaces obsolete mutable address edit; found actual rendering regression. Event.public_venue returns localized copy used by listing/detail/SEO, with exact AZ address, no legacy leak and unchanged stored snapshot.',
'test_event_address_is_localized_for_en_public_pages':'Same actual venue localization fix; exact English address and unchanged approved snapshot checked.',
'test_events_landing_does_not_render_filter_controls':'Stage27 calendar explicitly supports query/category/district/format/age controls. Assert actual supported controls rather than superseded absence.',
'test_catalog_filter_values_are_sorted_alphabetically':'Address-only district fixtures no longer conflict with Baku GPS; district aliases resolve canonical IDs. Exact stable IDs, alphabetic labels and metro order asserted.',
'test_home_page_uses_catalog_settings_districts':'Address-only fixture permits the intended legacy custom district; exact home option remains asserted.',
'test_catalog_card_uses_localized_district_instead_of_code':'Ağdaş address-only fixture no longer carries default Baku coordinates. Exact localized labels and absence of raw codes retained.',
'test_catalog_district_filter_matches_exact_value_only':'Address-only exact/similar district fixtures avoid point normalization; exact match included, similar district excluded.',
'test_catalog_map_serialization_includes_card_fields':'Current venue-point/member payload fully compared: stable IDs, coordinates, category icons/colors, district/metro codes and labels, contacts, rating, price, approved language fallback and schedule.',
'test_catalog_map_uses_only_filtered_map_ready_places':'Yasamal fixture point actually lies in Yasamal; one mapped and one address-only match. Full point/member transport comparison retained with canonical codes and separate labels.',
'test_catalog_price_filter_uses_range_overlap':'Accepted decision D10 removes incomparable budget filters. Legacy price parameters must not hide either fixture, and no price controls are rendered; tariff amounts remain explicit fixture data.',
'test_catalog_filters_hide_zero_options_and_show_public_counts':'Baku-wide fixture cards are address-only, district-specific fixture has its matching point; exact category/district/metro/subcategory counts retained.',
'test_home_hero_statistics_do_not_add_plus_to_exact_counts':'Hero counts businesses (map_business_count), not physical venue points; exact count and no plus signs retained.',
'test_home_map_search_text_includes_subcategory_name':'Map filtering moved to shared server endpoint. Real category/subcategory request returns exact member; unrelated category returns no points, instead of reading removed search_text field.',
'test_place_detail_page_includes_breadcrumb_and_aggregate_rating_schema':'Substantive approved Russian description/name and coherent address-only Yasamal fixture make Russian SEO eligible. Exact title, breadcrumb and AggregateRating retained.',
'test_sitemap_includes_all_languages_and_hreflang_alternates':'Fixture supplies substantive approved AZ/RU/EN content; all localized sitemap URLs and alternates remain required.',
'test_home_and_catalog_use_localized_strings_in_az_and_en':'Current copy follows accepted removal of budget filter; multilingual checks and absence of foreign-language copy retained.',
'test_review_models_disable_anonymous_flag_and_keep_author_name':'Place typed reviews preserve explicit anonymity and mask display name, while retaining internal author_name; legacy SiteReview still disables anonymity.',
}
readiness={
'test_every_requirement_blocks_publication_on_its_own':'All ten actual requirements tested independently at9/10 and90%; optional photo/GPS moved to explicit positive compatibility check; added real schedule omission.',
'test_gallery_photo_does_not_replace_the_main_photo':'Photo and GPS are optional by approved contract; no main-photo mutation, ready with gallery and with absent GPS.',
'test_instagram_and_website_do_not_replace_the_phone':'Business accepts website contact, Instagram handle alone still fails contact requirement.',
'test_publish_is_refused_with_the_concrete_missing_items':'Signed token reaches real readiness. Address-only card retains district, missing phone fails9/10 with exact field/message; no fictitious GPS requirement.',
'test_progress_never_reaches_hundred_while_an_issue_blocks_publication':'Required address/subcategory/contact each prevent100%; optional GPS no longer treated as blocking.',
}
entries=[]
for old in baseline['entries']:
    if old['id'].split('.')[2] not in modules:continue
    method=old['id'].split('.')[-1]
    note=notes.get(method)
    if old['id'].split('.')[2]=='place_readiness':
        note=readiness.get(method,'Approved readiness has ten required items, with photo/GPS optional. Exact progress, required-code set, field messages and form/shared-reader consistency updated; signed candidate token supplied where needed.')
    assert note, old['id']
    entries.append({'entry':old['entry'],'id':old['id'],'subtest':old.get('subtest',''),
        'initial_diagnosis':old['reason'],'change':note,
        'verification':'runs/public-media-green-04.json; final full host/image verification still required'})
assert len(entries)==47
(root/'docs/task33/completion/root-regression.json').write_text(json.dumps({'entries':entries,
    'extra_findings':['Immutable Event venue localization repaired.', 'Nizami street mistaken for district; one-pass localization with explicit regression tests.',
    'Sitemap lastmod expectation uses local date, eliminating UTC/Baku midnight mismatch.',
    'Two address-only count fixtures correctly remain off the home map.'],
    'qa_attempts':{'public-media-green-03':'Stopped with SIGINT and cleanup PASS: helper initially inserted on Place instead of Event before frozen-copy completion; corrected source and fresh green04 used.'}},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
