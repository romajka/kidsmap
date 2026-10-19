from pathlib import Path
Q=Path(__file__).resolve().parent;p=Q/'run_browser.py';t=p.read_text().replace("d=json.loads(r.stdout", "suffix='-'+sys.argv[2] if len(sys.argv)>2 else ''\nif suffix:(Q/(n+suffix+'-cli.txt')).write_text(r.stdout+r.stderr)\nd=json.loads(r.stdout");p.write_text(t)
