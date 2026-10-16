from pathlib import Path
import ast,hashlib,json,re,subprocess
root=Path.cwd();report=root/'docs/qa/admin-moderation-release-2026-10-16-r2';previous=root/'docs/qa/admin-moderation-release-2026-10-16-r1'
def read(n):return json.loads((report/(n+'.json')).read_text())
m=read('manifest');activation=read('activate');running=read('running');final=read('final');browser=read('browser')
# ssh_run names the local activation receipt activate.json; remote receipt is activation.json.
assert activation['status']=='ACTIVATED' and activation['running_source_MO_schema_check']
assert final['production_deployed'] and final['image_id']==read('build')['image_id']
assert final['old_image_preserved'] and all(final['protected_containers_unchanged'].values())
assert all(x==200 for x in final['health_checks'].values())
assert not final['migrations_run'] and not final['data_repair_run']
assert running['source_files_match']==len(m['files'])==973
assert running['MO']==read('candidate')['MO'] and running['system_check'] and running['pending_migrations']==0
snapshot=root/'.tmp/admin-moderation-release-2026-10-16-r2/release-source'
assert all(hashlib.sha256((snapshot/n).read_bytes()).hexdigest()==h for n,h in m['files'].items())
boundary=read('source-boundary')
local_differences=[n for n,h in m['files'].items()if hashlib.sha256((root/n).read_bytes()).hexdigest()!=h]
assert local_differences==boundary['local_preexisting_unreleased_paths']
assert all((root/n).read_bytes()==(root/'.tmp/admin-moderation-audit-2026-10-16-r1/source'/n).read_bytes()for n in local_differences)
assert activation['environment_unchanged'] and activation['env_file_unchanged'] and activation['mounts_unchanged']
assert subprocess.check_output(['git','rev-parse','HEAD'],text=True).strip()=='e4e05cc213b34e2d771ecb854901bfd016d1db51'
assert subprocess.run(['git','apply','--check','--reverse',str(report/'application.diff')],capture_output=True).returncode==0
assert re.search(r'Ran 158 tests in [0-9.]+s', (report/'exact-release-green.log').read_text())
assert '\nOK\n' in (report/'exact-release-green.log').read_text()
assert re.search(r'Ran 81 tests in 97.658s', (report/'places-green.log').read_text())
assert '\nOK\n' in (report/'places-green.log').read_text()
assert browser['pending_list_private_preview'] and browser['full_preview_rendered'] and browser['session_preserved'] and browser['review_workflow_rendered']
assert not browser['production_decisions_submitted'] and not browser['horizontal_overflow']
for p in report.glob('*.py'):ast.parse(p.read_text())
for p in [report/'REPORT.md', previous/'REPORT.md']:
 for target in re.findall(r'\]\(([^)]+)\)',p.read_text()):
  if target.startswith(('http','/')):continue
  assert (p.parent/target.split('#')[0]).exists(), target
scripts={p.name:hashlib.sha256(p.read_bytes()).hexdigest()for p in report.glob('*.py')}
(report/'script-manifest.json').write_text(json.dumps(scripts,indent=2))
result={'verified':True,'production_deployed':True,'image_id':final['image_id'],'source_files':973,'MO_files':3,
 'original_Django_tests':164,'affected_place_suite_repeated':81,'new_regression_tests':1,'local_WORKTREE_unique_targeted_tests_across_runs':165,'exact_release_tests_passed':158,'unreleased_extra_local_UI_tests_not_in_deployment':7,
 'original_native_flow_checks':54,'production_browser_GET_pass':True,'production_decisions_submitted':False,
 'full_project_suite_run':False,'models_migrations_changed':False,'current_local_HEAD_preserved':True,
 'deployment_provenance':'cfef63e3 + r1 patch 15cd43b75c1b + r2 patch 55917b04a917',
 'rollback_required':False,'backup_restore_drill':False}
(report/'verification.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
