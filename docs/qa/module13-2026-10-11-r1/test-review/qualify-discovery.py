import collections,json,pathlib,subprocess
P=pathlib.Path(__file__).resolve().parent;ROOT=P.parents[3]
donor=ROOT/'.tmp/module13-20261011-r1/test-review/head-donor'
(donor/'test_catalog.py').write_bytes(subprocess.check_output(['git','show','HEAD:test_catalog.py'],cwd=ROOT))
tracked=set(subprocess.check_output(['git','ls-files','src/catalog/testcases'],cwd=ROOT,text=True).splitlines())
discovery=json.loads((P/'discovery-audit.json').read_text())
def file_for(test_id):return 'src/'+test_id.rsplit('.',2)[0].replace('.','/')+'.py'
by_file=collections.Counter(file_for(x) for x in json.loads((P/'full-inventory.json').read_text())['ids'] if x not in set(discovery['ci_ids']))
rows=[{'path':f,'missing_cases':count,'tracked_at_HEAD':f in tracked} for f,count in sorted(by_file.items())]
qualification={'local_worktree_ci_missing':sum(x['missing_cases'] for x in rows),'local_missing_from_tracked_tests':sum(x['missing_cases'] for x in rows if x['tracked_at_HEAD']),'local_missing_from_untracked_tests':sum(x['missing_cases'] for x in rows if not x['tracked_at_HEAD']),'by_test_source':rows,'statement':'Current LOCAL WORKTREE command discovery; untracked corpus cannot be assumed present in GitHub. Actual GitHub execution NOT RUN.'}
(P/'discovery-corpus-qualification.json').write_text(json.dumps(qualification,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in qualification.items() if k!='by_test_source'},indent=2))
