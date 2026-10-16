from pathlib import Path
import json,hashlib,subprocess,shutil,urllib.request,re
h=Path(__file__).resolve().parent;r=h.parents[2];s=r/'.tmp'/h.name;entry=json.loads((h/'entry.json').read_text());approval=json.loads((h/'approval.json').read_text());pres=json.loads((h/'preservation.json').read_text())
expected=set(approval['existing_files'])|{'docs/qa/continuation-and-repair-prompts-2026-10-11.md'};assert set(pres['changed_entry_files'])==expected,pres['changed_entry_files'];assert not pres['missing_entry_files'];assert not pres['container_drift'];assert all(x.get('present')and x.get('same_args')and x.get('same_cwd')for x in pres['foreign_process_checks']);assert pres['head']==entry['head']and pres['branch']==entry['branch']and pres['active_run']==entry['active_run']
undo=s/'reverse-proof';undo.mkdir();
for name in expected:
 dest=undo/name;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(r/name,dest)
for name in ['approved-implementation.diff','status-update.diff']:
 p=subprocess.run(['patch','--batch','--reverse','-p1','-d',str(undo),'-i',str(h/name)],capture_output=True,text=True);(h/(name+'.reverse-proof.txt')).write_text(p.stdout+p.stderr);assert p.returncode==0
assert all(hashlib.sha256((undo/n).read_bytes()).hexdigest()==entry['files'][n]for n in expected)
meta=json.loads((h/'server-current.json').read_text());source=json.load(urllib.request.urlopen(meta['url']+'/qa/source/',timeout=5));assert source['pid']==meta['pid']and source['startup_matches_disk']and len(source['source'])==965;assert source['sole_locale_paths']==[str(s/'locales/locale')];(h/'runtime-source-final.json').write_text(json.dumps(source,indent=2))
result={'status':'LOCAL PASS MOD12/13 and completed module08 acceptance','source_files':965,'existing_application_files_changed':2,'new_tests':1,'status_guide_changed':True,'other_entry_files_unchanged':pres['unchanged_files'],'reverse_patch_restores_entry_hashes':True,'foreign_qa_http_preserved':len(pres['foreign_process_checks']),'containers_preserved':pres['entry_container_count'],'HEAD':pres['head'],'branch':pres['branch'],'active_run':pres['active_run'],'current_source_matches_runtime':True,'production_git_push_deploy':'NOT RUN in local QA; authorized release phase may now proceed'};(h/'final-gate.json').write_text(json.dumps(result,indent=2));print(json.dumps(result))
