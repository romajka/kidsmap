from pathlib import Path
O=Path('/mnt/c/kidsmap/docs/qa/module13-repair-2026-10-19-pc-r1')
t=(O/'browser-online-event.js').read_text().replace('a[href*="/events/3/"]','a[href*="/event/3-"]');t=t.replace('/png/online-','/png/online-r3-');(O/'browser-online-event-r3.js').write_text(t)
