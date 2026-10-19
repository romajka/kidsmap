import ast,difflib,hashlib,json,subprocess
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site22-pc-plan-r1';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
e=json.loads((O/'evidence/browser-destination-prototype-v2.json').read_text());assert all(all(r['checks'].values()) for r in e['rows']) and len(e['transport_rewrites'])==13
assert all(r['upstream_location']=='/admin/catalog/sitefootersettings/' for r in e['transport_rewrites'][:12])
assert e['transport_rewrites'][-1]['upstream_location']=='/admin/catalog/sitefootersettings/1/change/'
(O/'evidence/prototype-qualification.json').write_text(json.dumps({'v1':'12actual_hub_render failures: redirect GET route interception did not run; not product UI proof','v2':'12Save destination cases correct;13th rewritten footer POST was restoration with _continue. Restore data/log correct, navigation also simulated. Backend continue controls are separately PASS. No claim of native unmodified footer POST/redirect or actual-source GREEN.','v2_native_branding_saves':13,'v2_forwarded_footer_saves':13,'both_runs_expected_normal_fixture_logs':52,'candidate_builder_initial_error':'Expected12transport rewrites; actual13 includes restore. Inventory expectation corrected; no product assertion removed/changed.'},indent=2))
bad=[r for r in e['rows'] if 'baseline' in r and r['baseline']['document']>r['without_message']['document']];assert bad
if not (O/'candidate-v1.diff').exists():
 (O/'candidate-v1.diff').write_bytes((O/'proposed.diff').read_bytes());(O/'candidate-manifest-v1.json').write_bytes((O/'candidate-manifest.json').read_bytes())
rel='static/admin/css/pages/kidsmap_site_settings.css';before=(R/rel).read_bytes();extra=b'\r\n/* Saved subsection messages are shown on the settings hub. */\r\nbody:has(.km-site-settings-page) #content > .alert {\r\n  display: block;\r\n  min-width: 0;\r\n  max-width: 100%;\r\n  overflow-wrap: anywhere;\r\n}\r\n';after=before+extra
p=O/'candidate'/rel;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(after)
m=json.loads((O/'candidate-manifest.json').read_text());m['files'][rel]={'before_sha256':sha(R/rel),'candidate_sha256':sha(p)}
diff=b''
for path,d in m['files'].items():
 old=(R/path).read_bytes() if d['before_sha256'] else b'';new=(O/'candidate'/path).read_bytes();diff+=''.join(difflib.unified_diff(old.decode().splitlines(True),new.decode().splitlines(True),fromfile='a/'+path if old else '/dev/null',tofile='b/'+path)).encode()
(O/'proposed.diff').write_bytes(diff);m['diff_sha256']=sha(O/'proposed.diff');m['scope']='SITE22: six subsection normal Save exits to hub; hub-only alert wrapping required by actual destination prototype; persistent behavior regression tests';(O/'candidate-manifest.json').write_text(json.dumps(m,indent=2))
check=subprocess.run(['git','-C',str(R),'apply','--check',str(O/'proposed.diff')],capture_output=True,text=True);(Q/'candidate-final-apply-check.log').write_text(check.stdout+check.stderr);assert check.returncode==0,check.stderr
for rel in m['files']:
 p=O/'candidate'/rel
 if p.suffix=='.py':ast.parse(p.read_text())
 old=(R/rel).read_bytes().splitlines() if m['files'][rel]['before_sha256'] else [];new=p.read_bytes().splitlines()
 added=[line[2:] for line in difflib.ndiff([b.decode() for b in old],[b.decode() for b in new]) if line.startswith('+ ')]
 assert all(not line.endswith((' ','\t')) for line in added)
(O/'evidence/candidate-final-checks.json').write_text(json.dumps({'candidate_python_AST_parse':True,'git_apply_check_exit':0,'existing_source_CRLF_preserved':True,'added_lines_no_spaces_tabs_before_EOL':True,'existing_source_whitespace_retained':'Existing site.py blank-line trailing spaces kept byte-for-byte; initial whole-file audit incorrectly included baseline whitespace; only added lines audited','CRLF_parser_diagnostic':bool(check.stderr),'candidate_not_applied':True,'files':3},indent=2));print(json.dumps(m,indent=2))
