#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:8000}"
PWCLI="${PWCLI:-${CODEX_HOME:-$HOME/.codex}/skills/playwright/scripts/playwright_cli.sh}"
SESSION="kidsmap-mobile-nav-$$"

if [ ! -x "$PWCLI" ]; then
  echo "Playwright CLI wrapper not found: $PWCLI" >&2
  exit 1
fi

cleanup() {
  "$PWCLI" -s="$SESSION" close >/dev/null 2>&1 || true
}
trap cleanup EXIT

"$PWCLI" -s="$SESSION" open "$BASE_URL/"
RESULT="$("$PWCLI" -s="$SESSION" run-code "
async (page) => {
const widths = [360, 390, 430, 760];
const links = [
  ['Ana səhifə', '/', '/contacts/'],
  ['Kataloq', '/catalog/', '/'],
  ['Sahiblər üçün', '/for-business/', '/catalog/'],
  ['Layihə haqqında', '/about/', '/for-business/'],
  ['Əlaqə', '/contacts/', '/about/'],
];
const results = [];

for (const width of widths) {
  await page.setViewportSize({ width, height: 900 });
  await page.goto('${BASE_URL}/');

  const menu = page.locator('.mobile-nav-menu');
  const trigger = menu.locator('summary');

  await trigger.click();
  await page.keyboard.press('Escape');
  if (await menu.getAttribute('open') !== null) {
    throw new Error('Escape did not close the menu at ' + width + 'px');
  }

  await trigger.click();
  await page.mouse.click(width - 2, 898);
  if (await menu.getAttribute('open') !== null) {
    throw new Error('Outside click did not close the menu at ' + width + 'px');
  }

  for (const [name, expectedPath, startPath] of links) {
    await page.goto('${BASE_URL}' + startPath);
    await trigger.click();

    const link = menu.getByRole('link', { name, exact: true });
    const hit = await link.evaluate((element) => {
      const rect = element.getBoundingClientRect();
      const target = document.elementFromPoint(
        rect.left + rect.width / 2,
        rect.top + rect.height / 2,
      );
      return {
        tag: target ? target.tagName : null,
        inDropdown: Boolean(target && target.closest('.mobile-nav-dropdown')),
        isLink: Boolean(target && target.closest('a') === element),
      };
    });

    if (!hit.inDropdown || !hit.isLink) {
      throw new Error(
        'Hit testing failed for ' + name + ' at ' + width + 'px: ' + JSON.stringify(hit),
      );
    }

    await link.click();
    await page.waitForURL((url) => url.pathname === expectedPath);
    if (await page.evaluate(() => window.location.pathname) !== expectedPath) {
      throw new Error('Navigation failed for ' + name + ' at ' + width + 'px');
    }

    results.push({ width, name, path: expectedPath, hit: hit.tag });
  }
}

return results;
}
")"

printf '%s\n' "$RESULT"
if [[ "$RESULT" == *"### Error"* ]]; then
  exit 1
fi
