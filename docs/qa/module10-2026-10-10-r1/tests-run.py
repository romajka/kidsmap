from pathlib import Path
import subprocess,json,re,datetime,os,sys,time,shutil
P=Path(__file__).resolve().parent;R=P.parents[2];sys.stdout.reconfigure(encoding='utf-8')
labels=['test_public_section_switches','events_feature','specialists.TestSpecialistsFeatureFlag','test_site_whatsapp','test_public_favorite_count','test_home_public_metrics','test_task33_home_map','public.PublicLanguageConsistencyTests','admin.TestSiteGalleryImageAdminMedia','admin.TestAdminSidebarStructure.test_hidden_public_sections_remain_available_in_admin']
stem='tests'
if len(sys.argv)>1 and sys.argv[1]=='pages':
 stem='pages-tests'
 labels=['public.TestPublicPagesSmoke.'+s for s in ['test_add_place_and_legal_pages_open_in_languages','test_add_place_page_explains_free_listing_moderation_and_actions_in_all_languages','test_legacy_for_business_url_redirects_permanently_to_add_place','test_privacy_policy_is_full_document_in_all_languages','test_terms_of_use_is_full_document_in_all_languages','test_terms_page_mentions_public_sources_disclaimer','test_listing_rules_is_full_document_in_all_languages','test_ru_footer_privacy_link_points_to_ru_privacy','test_about_page_shows_extended_project_description','test_faq_page_loads_in_all_languages','test_faq_page_has_no_russian_copy_in_azerbaijani_or_english','test_legacy_az_urls_redirect_to_default_language_without_prefix']]
cmd=[str(R/'.venv/Scripts/python.exe'),str(P/'run.py'),'test',*['catalog.testcases.'+s for s in labels]]
env=os.environ.copy();env.update(PYTHONUTF8='1',PYTHONIOENCODING='utf-8');start=time.monotonic()
r=subprocess.run(cmd,cwd=R,capture_output=True,text=True,encoding='utf-8',errors='replace',env=env)
s=r.stdout+'\n'+r.stderr
s,n=re.subn(r'(name=["\']csrfmiddlewaretoken["\']\s+value=["\'])[^"\']+',r'\1[LOCAL-CSRF-REDACTED]',s)
if (P/(stem+'.log')).exists():
 i=1
 while (P/(stem+f'.attempt{i}.log')).exists():i+=1
 shutil.copyfile(P/(stem+'.log'),P/(stem+f'.attempt{i}.log'))
 shutil.copyfile(P/(stem+'-command.json'),P/(stem+f'-command.attempt{i}.json'))
(P/(stem+'.log')).write_text(s,encoding='utf-8');(P/(stem+'-command.json')).write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':cmd,'exit_code':r.returncode,'csrf_redactions':n,'duration_seconds':round(time.monotonic()-start,2),'unit_public_base_url':'http://testserver'},indent=2),encoding='utf-8')
print('Native exit',r.returncode)
for line in s.splitlines():
 if re.match(r'^(Ran |FAILED|OK|FAIL:|ERROR:|Found |System check)',line):print(line[:300])
sys.exit(r.returncode)
