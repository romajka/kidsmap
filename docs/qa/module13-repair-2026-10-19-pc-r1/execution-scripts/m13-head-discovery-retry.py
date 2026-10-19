from pathlib import Path
import subprocess,json
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m13-full-r1';O=R/'docs/qa/module13-repair-2026-10-19-pc-r1';D=Q/'head-donor';P=Q/'head-profile';output=D/'.tmp/locales-current';output.parent.mkdir(exist_ok=True)
cmd=['python3',str(R/'scripts/build_isolated_locales.py'),'build','--source-locale',str(D/'locale'),'--output',str(output),'--compiler','native'];p=subprocess.run(cmd,capture_output=True,text=True);assert p.returncode==0,p.stderr
t=(P/'settings.py').read_text().replace(str(Q/'head-locales/locale'),str(output/'locale'));(P/'settings.py').write_text(t)
t=(P/'discover.py').read_text().replace("Q/'head-locales/manifest.json'","D/'.tmp/locales-current/manifest.json'");(P/'discover.py').write_text(t)
p=subprocess.run(['docker','exec','m13qa04-r4-app','python',str(P/'discover.py')],capture_output=True,text=True);(Q/'head-discovery-r2.log').write_text(p.stdout+p.stderr);assert p.returncode==0,p.stderr
d=json.loads((Q/'head-discovery.json').read_text());d['snapshot']={'head':subprocess.check_output(['/mnt/c/Program Files/Git/cmd/git.exe','-C','C:/kidsmap','rev-parse','HEAD'],text=True).strip(),'archive_source_only':True,'database':'Isolated in-memory SQLite configured; discovery only, no migrations or test bodies','real_GitHub':'NOT RUN','first_attempt':'HEAD compiler correctly rejected a locale manifest outside donor .tmp; fresh donor-owned locale output used without changing HEAD source.'};(O/'evidence/head-discovery.json').write_text(json.dumps(d,indent=2));print(p.stdout)
