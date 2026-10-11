"""Repair own harness selectors, never application source."""
from pathlib import Path
here=Path(__file__).resolve().parent
p=here/'multiple.js'
s=p.read_text(encoding='utf-8')
s=s.replace("a.locator('details.pc-offering-translations').last()", "a.locator(':scope > details.pc-offering-translations').first()")
p.write_text(s,encoding='utf-8')
print('Own activity translation selector corrected.')
p=here/'roundtrip.js'
s=p.read_text(encoding='utf-8')
s=s.replace("await p.waitForTimeout(700);const message", "await p.waitForTimeout(700);if(await p.getByRole('button',{name:'Продолжить импорт',exact:true}).count())await p.getByRole('button',{name:'Продолжить импорт',exact:true}).click();await p.waitForTimeout(500);const message")
p.write_text(s,encoding='utf-8')
print('Own import confirmation native step added.')
p=here/'clipping.js'
s=p.read_text(encoding='utf-8')
s=s.replace('rows=[];p.setDefaultTimeout', "rows=[],consoleRecords=[],httpErrors=[],pageErrors=[];p.on('console',m=>{if(['error','warning'].includes(m.type()))consoleRecords.push({type:m.type(),text:m.text().slice(0,240)});});p.on('pageerror',e=>pageErrors.push(String(e)));p.on('response',r=>{if(r.status()>=400)httpErrors.push({path:new URL(r.url()).pathname,status:r.status()});});p.setDefaultTimeout")
s=s.replace('return{rows};', 'return{rows,consoleRecords,httpErrors,pageErrors};')
p.write_text(s,encoding='utf-8')
print('Own console/network observational recorder enabled.')
p=here/'clipping.js'
s=p.read_text(encoding='utf-8').replace('/hidden|clip/.test(s.overflowX)', '/hidden|clip|auto|scroll/.test(s.overflowX)')
p.write_text(s,encoding='utf-8')
print('Own clipping metric includes scrollable tabs; initial visibility measured, scroll reachability recorded separately.')
