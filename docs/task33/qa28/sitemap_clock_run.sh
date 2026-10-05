#!/bin/bash
set -euo pipefail
root=/mnt/c/kidsmap
checkout=/root/km28-sitemap-probe
output=/tmp/task33-stage28-sitemap-clock-final1
retained=/root/task33-evidence/stage28-sitemap-clock-final1-20261004
test ! -e "$checkout"
test ! -e "$output"
test ! -e "$retained"
cp -a /root/km28-image-context3 "$checkout"
ln -s /root/kidsmap-task33/.venv "$checkout/.venv"
cp "$root/docs/task33/qa28/sitemap_clock_probe.py" "$checkout/src/catalog/testcases/test_qa28_sitemap_clock_probe.py"
cd "$checkout"
set +e
.venv/bin/python docs/task33/qa04/run.py --mode all --output "$output" --label catalog.testcases.test_qa28_sitemap_clock_probe.SitemapClockProbe
result=$?
set -e
test -d "$output" && cp -a "$output" "$retained"
.venv/bin/python "$root/docs/task33/qa28/security_collect.py" "$retained" "$root/docs/task33/reports/28-sitemap-clock-results.json" "External QA-only deterministic UTC/Baku replay of original unchanged legacy sitemap assertion"
exit "$result"
