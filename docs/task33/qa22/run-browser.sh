#!/bin/bash
set -euo pipefail
cd /root/task33-browser-tools
export PATH=/root/task33-browser-tools/node_modules/.bin:$PATH
stamp=${1:?Unique stamp required}
payload=${2:-probe}
[[ "$stamp" =~ ^[a-zA-Z0-9-]+$ ]]
[[ "$payload" == probe || "$payload" == matrix || "$payload" == flows || "$payload" == diagnose || "$payload" == admin ]]
root=/tmp/task33-browser22-$stamp
evidence=/root/task33-evidence/browser22-$stamp
test ! -e "$root"
test ! -e "$evidence"
mkdir -p "$evidence" /root/kidsmap-task33/docs/task33/qa22
cp -r /mnt/c/kidsmap/docs/task33/qa22/. /root/kidsmap-task33/docs/task33/qa22/
python3 /root/kidsmap-task33/docs/task33/qa22/cache-font.py
/root/kidsmap-task33/.venv/bin/python /root/kidsmap-task33/docs/task33/qa22/browser.py --mode probe --output "$root" > "$evidence/launcher.log" 2>&1 &
launcher_pid=$!
finish() {
  if test -f "$root/browser-ready.json" && ! test -f "$root/run.json"; then
    curl --max-time 15 -fsS "http://127.0.0.1:8782/qa22/finish?token=$(basename "$root")" >/dev/null || true
  fi
  wait "$launcher_pid" || true
  if test -f "$root/run.json"; then
    mkdir -p "$evidence/launcher"
    cp -r "$root/." "$evidence/launcher/"
  fi
}
trap finish EXIT
for i in $(seq 1 180); do
  if test -f "$root/browser-ready.json"; then break; fi
  if ! kill -0 "$launcher_pid" 2>/dev/null; then cat "$evidence/launcher.log"; exit 2; fi
  sleep 1
done
test -f "$root/browser-ready.json"
npx playwright-cli -s=qa22 snapshot > "$evidence/initial-snapshot.txt"
sed "s|__QA22_EVIDENCE__|$evidence|g" /root/kidsmap-task33/docs/task33/qa22/$payload.js > "$evidence/$payload.js"
npx playwright-cli -s=qa22 run-code --filename "$evidence/$payload.js" > "$evidence/result-cli.txt"
npx playwright-cli -s=qa22 snapshot > "$evidence/final-snapshot.txt"
npx playwright-cli -s=qa22 console error > "$evidence/console-cli.txt"
npx playwright-cli -s=qa22 requests > "$evidence/requests-cli.txt"
finish
wait "$launcher_pid"
python3 /root/kidsmap-task33/docs/task33/qa22/summarize.py "$evidence"
