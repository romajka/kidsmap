import subprocess,os,json,sys,datetime
from pathlib import Path
P=Path(__file__).resolve().parent;R=P.parents[2]
labels=['test_task33_search','test_task33_map','test_task33_home_map','test_public_filter_consistency','test_place_sorting_and_filtering','test_search_engine_verification','test_home_public_metrics','test_public_section_switches','test_task33_public_details','test_task33_event_public','test_living_map']
cmd=[str(R/'.venv/Scripts/python.exe'),str(P/'run.py'),'test',*['catalog.testcases.'+x for x in labels]]
env=os.environ.copy();env.update(PYTHONUTF8='1',PYTHONIOENCODING='utf-8')
r=subprocess.run(cmd,cwd=R,capture_output=True,encoding='utf-8',errors='replace',env=env)
(P/'tests.log').write_text(r.stdout+'\n'+r.stderr,encoding='utf-8')
(P/'tests-command.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'command':cmd,'exit_code':r.returncode},indent=2),encoding='utf-8')
print('exit',r.returncode);print((r.stdout+'\n'+r.stderr)[-4500:]);sys.exit(r.returncode)
