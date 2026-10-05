"""Portable Linux/WSL synthetic preview; never imports the checkout's .env."""
import hashlib,json,os,sys,time,urllib.request,subprocess
from pathlib import Path

os.environ['KIDSMAP_MANUAL_PORTABLE']='1'
from start import HERE,ROOT,STATE,PORT,main

if __name__=='__main__':
    if sys.platform!='linux':raise SystemExit('Run in Linux/WSL; see ../TRANSFER.md')
    STATE.mkdir(exist_ok=True)
    if len(sys.argv)>1 and sys.argv[1]=='stop':
        main();sys.exit(0)
    # Git can normalise CRLF on another OS. Record the current checkout's
    # actual bytes in local state, without rewriting historical QA evidence.
    prior=json.loads((HERE.parent/'source-manifest.json').read_text())['source_files']
    files=[{'path':i['path'],'sha256':hashlib.sha256((ROOT/i['path']).read_bytes()).hexdigest()} for i in prior]
    (STATE/'source-manifest.json').write_text(json.dumps({'source_files':files},indent=2)+'\n')
    # Compile only the app catalogues, never historical snapshots or venvs.
    for po in sorted((ROOT/'locale').glob('*/LC_MESSAGES/*.po')):
        subprocess.run(['msgfmt','--check-format','-o',str(po.with_suffix('.mo')),str(po)],
                       env={'PATH':'/usr/bin:/bin','LANG':'C.UTF-8'},check=True)
    main()
    for _ in range(180):
        try:
            with urllib.request.urlopen(f'http://127.0.0.1:{PORT}/qa/fixtures.json',timeout=2) as r:
                if r.status==200:break
        except OSError:time.sleep(1)
    else:raise SystemExit('Preview not ready; see '+str(STATE/'server.log'))
    print(f'READY http://localhost:{PORT}/qa/ | admin: /admin/ | demo_moderator / KidsMap-local-2026')
