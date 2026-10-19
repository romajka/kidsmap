from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;F=R/'docs/qa/site-qa19-fix-2026-10-18-pc-r1'
for old,new in [('browser-flows-final.js','browser-json-flows.js'),('browser-mobile-errors.js','browser-mobile-errors.js')]:
 text=(F/old).read_text().replace('33540','33560').replace('site-qa19-fix-2026-10-18-pc-r1','site-qa21-fix-2026-10-18-pc-r1').replace('/qa/site19/','/qa/site21/').replace("'/png/flow-final-'","'/png/json-flow-'")
 if old=='browser-mobile-errors.js':
  text=text.replace("no_json_or_log_write:JSON.stringify(before)===JSON.stringify(after)","no_json_or_log_write:JSON.stringify(before)===JSON.stringify(after),no_horizontal_overflow:geometry.document<=geometry.viewport,textarea_within_viewport:geometry.textarea.left>=0&&geometry.textarea.right<=geometry.viewport")
 (O/new).write_text(text)
print('Own JSON/invalid/retry/mobile scripts prepared from preserved passing SITE19 harness; no app change')
