from pathlib import Path
p=Path(__file__).resolve().parent/'public-native.js';s=p.read_text(encoding='utf-8')
s=s.replace("if(width<=768&&await p.locator('[data-filters-open]').first().isVisible())await p.locator('[data-filters-open]').first().click();", "if(width<=760){await p.locator('[data-filters-open]:visible').first().click();await p.waitForTimeout(300);}")
s=s.replace("if(width<=768){await p.locator('#filters-form button[type=submit]').click();}","if(width<=760){await p.locator('#filters-form button[type=submit]').click();}")
p.write_text(s,encoding='utf-8');print('Own QA: exact actual max760 mobile breakpoint; use visible filter trigger.')
