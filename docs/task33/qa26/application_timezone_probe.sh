#!/bin/bash
set -euo pipefail
cd /root/task33-browser-tools
npx playwright-cli -s=qa26tz open about:blank >/root/task33-evidence/qa26-tz-probe-open.txt
trap 'npx playwright-cli -s=qa26tz close >/root/task33-evidence/qa26-tz-probe-close.txt' EXIT
npx playwright-cli -s=qa26tz run-code --filename /mnt/c/kidsmap/docs/task33/qa26/application_timezone_probe.js
