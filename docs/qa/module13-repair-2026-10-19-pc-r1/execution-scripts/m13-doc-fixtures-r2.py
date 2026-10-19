from pathlib import Path
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m13-full-r1';O=R/'docs/qa/module13-repair-2026-10-19-pc-r1'
for name,data in [('invalid.txt',b'FICTIONAL not an allowed document'),('corrupt.png',b'not a real png'),('oversize.pdf',b'%PDF-1.7\n'+b'0'*(12*1024*1024))]:(Q/'assets'/name).write_bytes(data)
t=(O/'browser-private-documents.js').read_text().replace("employee:'editor'","employee:'editor',author:'owner',admin:'admin'")
t=t.replace('/png/','/png/doc-r2-');(O/'browser-private-documents-r2.js').write_text(t)
