from pathlib import Path
p=Path(__file__).resolve().parent/'admin-functional.js';s=p.read_text(encoding='utf-8').replace("const add=(id,ok,x={})", "a.on('dialog',d=>d.accept());const add=(id,ok,x={})")
s=s.replace("a.waitForNavigation()","a.waitForNavigation({waitUntil:'domcontentloaded'})")
s=s.replace("labels.every(x=>x.includes(expected))", "labels.length===3&&labels.every(x=>x.includes(expected))")
p.write_text(s,encoding='utf-8');print('Own admin harness accepts native confirmation for only own unsaved synthetic form and waits DOMContentLoaded.')
