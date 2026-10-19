from pathlib import Path
O=Path('/mnt/c/kidsmap/docs/qa/module13-repair-2026-10-19-pc-r1')
t=(O/'browser-event-lifecycle.js').read_text().replace("a.locator('[data-main-photo-root] a')","a.locator('[data-main-photo-root] a.km-media-main__view')")
needle="check('format-toggle-retains-address',await p.locator('[name=address]').inputValue()==='Uydurma küçə 41');"
assert needle in t;t=t.replace(needle,needle+"await p.locator('[name=venue_choice_switch][value=related]').check();await p.locator('[name=related_place]').selectOption('2');")
t=t.replace('/png/event-lifecycle-','/png/event-lifecycle-r2-');(O/'browser-event-lifecycle-r2.js').write_text(t)
