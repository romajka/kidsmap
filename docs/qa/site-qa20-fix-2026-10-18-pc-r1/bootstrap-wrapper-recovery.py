from pathlib import Path
R=Path('/mnt/c/kidsmap');P=R/'docs/qa/site-qa20-recheck-2026-10-18-pc-r1'
s=(P/'bootstrap.py').read_text()
s=s.replace("P=R/'docs/qa/site-qa22-fix-2026-10-18-pc-r1'","P=R/'docs/qa/site-qa20-recheck-2026-10-18-pc-r1'")
s=s.replace("O=R/'docs/qa/site-qa20-recheck-2026-10-18-pc-r1'","O=R/'docs/qa/site-qa20-fix-2026-10-18-pc-r1'").replace("Q=R/'.tmp/site20-pc-plan-r1'","Q=R/'.tmp/site20-pc-fix-r1'")
s=s.replace("app='m10s20-plan-r1-app';db='m10s20_plan_r1';tdb='test_m10s20_plan_r1'","app='m10s20-fix-r1-app';db='m10s20_fix_r1';tdb='test_m10s20_fix_r1'").replace('33620','33630')
start=s.index('def adapt(s):');end=s.index("(Q/'stage.json')",start)
s=s[:start]+'''def adapt(s):
 for a,b in [('site20-pc-plan-r1','site20-pc-fix-r1'),('site-qa20-recheck-2026-10-18-pc-r1','site-qa20-fix-2026-10-18-pc-r1'),('m10s20_plan_r1','m10s20_fix_r1'),('m10s20-plan-r1','m10s20-fix-r1'),('33620','33630')]:s=s.replace(a,b)
 return s
for name in ['qa_settings.py','runtime.py','qa_urls.py','seed.py','proxy.py','playwright.json']:(Q/name).write_text(adapt((P/name).read_text()))
(Q/'test_site19_candidate.py').write_bytes((R/'docs/qa/site-qa22-fix-2026-10-18-pc-r1/test_site19_candidate.py').read_bytes())
for name in ['start_server.py','browser_driver.py','normal_migrate.py','run_red.py','browser-baseline.js']:(O/name).write_text(adapt((P/name).read_text()))
(O/'test_site20_candidate.py').write_bytes((P/'test_site20_candidate.py').read_bytes())
(Q/'test_site20_candidate.py').write_bytes((P/'test_site20_candidate.py').read_bytes())
(O/'implemented.diff').write_bytes((P/'proposed.diff').read_bytes())
(O/'approved-candidate-manifest.json').write_bytes((P/'candidate-manifest.json').read_bytes())
(O/'IMPLEMENTATION_PLAN.md').write_bytes((P/'IMPLEMENTATION_PLAN.md').read_bytes())
(O/'authorization.json').write_text(json.dumps({'human':'принимаем','meaning':'explicit approval of exact2file SITE20 plan after direct scope question','plan_sha256':sha(P/'IMPLEMENTATION_PLAN.md'),'diff_sha256':sha(P/'proposed.diff'),'scope':list(read(P/'candidate-manifest.json')['files'])},ensure_ascii=False,indent=2))
''' +s[end:]
O=R/'docs/qa/site-qa20-fix-2026-10-18-pc-r1'
(O/'bootstrap-wrapper-initial.py').write_bytes(Path(__file__).read_bytes())
(O/'bootstrap.py').write_text(s)
