#!/bin/bash
set -euo pipefail
cd /root/task33-browser-tools
export PATH=/root/task33-browser-tools/node_modules/.bin:$PATH
stamp=${1:?Unique stamp required}
[[ "$stamp" =~ ^[a-zA-Z0-9-]+$ ]]
root=/tmp/task33-browser24-$stamp
evidence=/root/task33-evidence/browser24-$stamp
test ! -e "$root"
test ! -e "$evidence"
mkdir -p "$evidence" /root/km24-security/docs/task33/qa24/browser_bridge
cp /mnt/c/kidsmap/docs/task33/qa24/browser.py /mnt/c/kidsmap/docs/task33/qa24/browser-matrix.js /root/km24-security/docs/task33/qa24/
cp /mnt/c/kidsmap/docs/task33/qa24/browser_bridge/commands.py /root/km24-security/docs/task33/qa24/browser_bridge/
test -f /root/task33-browser-tools/material22.css
test -f /root/task33-browser-tools/material.ttf
/root/km24-security/.venv/bin/python /root/km24-security/docs/task33/qa24/browser.py --mode probe --output "$root" > "$evidence/launcher.log" 2>&1 &
launcher_pid=$!
finish() {
 if test -f "$root/browser-ready.json" && ! test -f "$root/run.json"; then
  curl --max-time 15 -fsS "http://127.0.0.1:8784/qa24/finish?token=$(basename "$root")" >/dev/null || true
 fi
 wait "$launcher_pid" || true
 if test -f "$root/run.json"; then mkdir -p "$evidence/launcher";cp -r "$root/." "$evidence/launcher/";fi
}
trap finish EXIT
for i in $(seq 1 180); do
 if test -f "$root/browser-ready.json"; then break;fi
 if ! kill -0 "$launcher_pid" 2>/dev/null;then cat "$evidence/launcher.log";exit 2;fi
 sleep 1
done
test -f "$root/browser-ready.json"
npx playwright-cli -s=qa24 open about:blank > "$evidence/open-cli.txt"
npx playwright-cli -s=qa24 snapshot > "$evidence/initial-snapshot.txt"
matrix=${2:-/root/km24-security/docs/task33/qa24/browser-matrix.js}
sed "s|__QA24_EVIDENCE__|$evidence|g" "$matrix" > "$evidence/matrix.js"
npx playwright-cli -s=qa24 run-code --filename "$evidence/matrix.js" > "$evidence/result-cli.txt"
npx playwright-cli -s=qa24 snapshot > "$evidence/final-snapshot.txt"
npx playwright-cli -s=qa24 console error > "$evidence/console-cli.txt"
npx playwright-cli -s=qa24 requests > "$evidence/requests-cli.txt"
finish
wait "$launcher_pid"
