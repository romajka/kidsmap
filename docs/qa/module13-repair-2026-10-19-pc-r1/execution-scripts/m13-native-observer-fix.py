from pathlib import Path
R=Path('/mnt/c/kidsmap');O=R/'docs/qa/module13-repair-2026-10-19-pc-r1'
t=(O/'browser-event-green.js').read_text()
t=t.replace("await p.keyboard.press('Enter');await p.waitForLoadState('domcontentloaded');", "await Promise.all([p.waitForURL(B+s.urls[lang].event),p.keyboard.press('Enter')]);await p.waitForLoadState('domcontentloaded');")
t=t.replace("conflict:staleres.status()===409", "conflict:staleres.status()===200&&await stale.locator('[data-error-code=stale_version]').count()===1")
needle="for(const lang of ['az','ru','en'])for(const width"
initial="""await owner.p.goto(manage);await owner.p.locator('[name=start_datetime]').fill('2026-11-02T12:00');await owner.p.locator('[name=end_datetime]').fill('2026-11-02T13:00');await owner.p.locator('[name=reason]').fill('Native physical upcoming transfer');const[first]=await Promise.all([owner.p.waitForResponse(r=>r.request().method()==='POST'),owner.p.locator('button[formaction$=\"/reschedule/\"]').click()]);await owner.p.waitForLoadState('domcontentloaded');rows.push({id:'physical-native-first-reschedule',checks:{saved:first.status()===302}});
  """
assert needle in t;t=t.replace(needle,initial+needle);t=t.replace('/png/event-green-','/png/event-green-r2-')
(O/'browser-event-green-r2.js').write_text(t)
(O/'evidence/native-observer-correction.md').write_text('Initial GREEN observer checked URL/DOM before navigation was committed; waitForLoadState on the prior document is not a navigation wait. Added waitForURL around keyboard Enter. Stale-version form intentionally renders HTTP200 with data-error-code=stale_version, not409; observer corrected after source verification. No application fix or old assertion change. Initial failed suite retained/excluded from acceptance. Audited cancelled event1 retained, separate fresh physical/online identities used, no ORM replay/repair.\n')
