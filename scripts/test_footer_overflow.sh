#!/usr/bin/env bash
set -euo pipefail

BASE_URL="${1:-http://127.0.0.1:8000}"
PWCLI="${PWCLI:-${CODEX_HOME:-$HOME/.codex}/skills/playwright/scripts/playwright_cli.sh}"
SESSION="kidsmap-footer-overflow-$$"

if [ ! -x "$PWCLI" ]; then
  echo "Playwright CLI wrapper not found: $PWCLI" >&2
  exit 1
fi

cleanup() {
  "$PWCLI" -s="$SESSION" close >/dev/null 2>&1 || true
}
trap cleanup EXIT

"$PWCLI" -s="$SESSION" open "$BASE_URL/catalog/"
RESULT="$("$PWCLI" -s="$SESSION" run-code "
async (page) => {
  const viewports = [
    { width: 768, height: 1024 },
    { width: 390, height: 844 },
  ];
  const paths = ['/catalog/', '/ru/catalog/', '/en/catalog/'];
  const results = [];

  for (const viewport of viewports) {
    await page.setViewportSize(viewport);

    for (const path of paths) {
      await page.goto('${BASE_URL}' + path);
      const measurement = await page.locator('.site-footer').evaluate((footer) => {
        const footerRect = footer.getBoundingClientRect();
        const outside = Array.from(footer.querySelectorAll('*'))
          .filter((element) => {
            const rect = element.getBoundingClientRect();
            return rect.left < footerRect.left - 1 || rect.right > footerRect.right + 1;
          })
          .map((element) => element.className || element.tagName);

        return {
          clientWidth: footer.clientWidth,
          scrollWidth: footer.scrollWidth,
          left: footerRect.left,
          right: footerRect.right,
          outside,
        };
      });

      if (measurement.scrollWidth > measurement.clientWidth + 1 || measurement.outside.length) {
        throw new Error(
          'Footer overflow at ' + viewport.width + 'x' + viewport.height + ' ' + path + ': ' +
          JSON.stringify(measurement),
        );
      }

      results.push({ viewport, path, measurement });
    }
  }

  return results;
}
")"

printf '%s\n' "$RESULT"
if [[ "$RESULT" == *"### Error"* ]]; then
  exit 1
fi
