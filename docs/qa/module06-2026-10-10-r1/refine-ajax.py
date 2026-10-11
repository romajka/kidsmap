from pathlib import Path
p=Path(__file__).resolve().parent/'functional.js';s=p.read_text(encoding='utf-8')
s=s.replace("p.waitForNavigation({waitUntil:'domcontentloaded'})","p.waitForResponse(r=>r.url().includes('/catalog/')&&r.request().method()==='GET')")
s=s.replace("next.click()]);const second", "next.click()]);await p.waitForTimeout(500);const second")
s=s.replace("search.press('Enter')]);add", "search.press('Enter')]);await p.waitForTimeout(500);add")
s=s.replace("p.locator('.active-filter-reset').click()]);add", "p.locator('.active-filter-reset').click()]);await p.waitForTimeout(500);add")
s=s.replace("p.locator('[data-sort-value=reviews_desc]').click()]);add", "p.locator('[data-sort-value=reviews_desc]').click()]);await p.waitForTimeout(500);add")
p.write_text(s,encoding='utf-8');print('Own harness now waits for GET response and rendered replacement for actual desktop AJAX transport.')
