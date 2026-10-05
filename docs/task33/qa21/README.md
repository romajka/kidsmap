# Stage21 isolated rendered QA

`browser.py` wraps the unchanged QA04 launcher, prepending a synthetic browser
bridge. PostgreSQL remains disposable, network-none, tmpfs and Unix-socket only;
application outbound guards remain installed. The bridge exposes only fixed
synthetic public routes, one generated fixture image, static finder resources,
cached public font files and `/finish` on `127.0.0.1:8781`. No production env,
accounts, media or database are read.

Local tools live outside the repository in `/root/task33-browser-tools`:
Node22, `@playwright/cli`, Playwright Chromium, cached Material Symbols font.
Run `cache-font.py` during setup to populate this public asset cache; browser
runtime rewrites the font request to loopback. Other external scripts are
explicitly stubbed with empty bodies, and kidsmap.az navigation is intercepted
and served from the loopback bridge. External widgets/integrations are not
validated.

Compile existing gettext catalogs locally before browser runs. The bridge
explicitly enables localized place paths and `https://kidsmap.az` canonical
display URLs in the disposable child. Those URLs never contact the real site.

Run from WSL Ubuntu24.04 after the orchestrator has frozen and mirrored source:

```bash
export PATH=/root/task33-browser-tools/node_modules/.bin:$PATH
cd /root/task33-browser-tools
npx playwright-cli -s=qa21 open about:blank --browser chromium
cp /mnt/c/kidsmap/docs/task33/qa21/run-browser.sh /root/task33-browser-tools/run-browser-frozen.sh
bash /root/task33-browser-tools/run-browser-frozen.sh UNIQUE-STAMP
bash /root/task33-browser-tools/run-browser-frozen.sh SECOND-UNIQUE-STAMP final-smoke
```

Do not edit the executing shell script. Each output stamp must be new. The helper
copies only qa21 files into the Linux source mirror; application source mirroring
is owned by the orchestrator. CLI run-code executes actual rendered browser
assertions; it does not use jsdom or `@playwright/test` specs.

Matrix: five public surfaces × AZ/RU/EN ×320/360/390/768/1024/1280/1440 =105
pages. Checks cover canonical/hreflang/schema, approved translation fallback and
closed notices, malicious script termination text, translated shell headings,
stable review/media facts, layout overflow, font loading, language switch URLs,
console/network/static failures and legacy redirects. Final smoke checks15
entity pages and keyboard desktop/mobile language navigation on final source.

Evidence is retained outside Git under `/root/task33-evidence/browser21-STAMP`;
raw Django outputs initially use `/tmp` and are copied only after launcher
completion. Read `launcher/run.json` for child and cleanup status. Screenshot
copies for visual inspection may use ignored `output/playwright/qa21/`.
