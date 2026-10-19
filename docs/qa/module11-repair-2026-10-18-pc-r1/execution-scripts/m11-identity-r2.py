from pathlib import Path
O=Path('/mnt/c/kidsmap/docs/qa/module11-repair-2026-10-18-pc-r1');t=(O/'browser-identity.js').read_text();t=t.replace('rows=[],errors=[],pageerrors=[]','rows=[],errors=[],pageerrors=[],dialogs=[]');t=t.replace("p.on('pageerror',e=>pageerrors.push(String(e)));", "p.on('pageerror',e=>pageerrors.push(String(e)));p.on('dialog',async d=>{dialogs.push({type:d.type(),message:d.message()});await d.accept();});")
t=t.replace('return{rows,errors,pageerrors,scope:', 'return{rows,errors,pageerrors,dialogs,scope:');(O/'browser-identity-r2.js').write_text(t)
