#!/bin/bash
set -euo pipefail
cd /root/task33-browser-tools
export PATH=/root/task33-browser-tools/node_modules/.bin:$PATH
mkdir -p /root/kidsmap-task33/docs/task33/qa21
cp -r /mnt/c/kidsmap/docs/task33/qa21/. /root/kidsmap-task33/docs/task33/qa21/
stamp=${1:?Pass a unique evidence stamp}
payload=${2:-matrix}
[[ "$payload" == matrix || "$payload" == final-smoke ]]
[[ "$stamp" =~ ^[a-zA-Z0-9-]+$ ]]
root=/tmp/task33-browser21-$stamp
evidence=/root/task33-evidence/browser21-$stamp
test ! -e "$root"
test ! -e "$evidence"
mkdir -p "$evidence"
/root/kidsmap-task33/.venv/bin/python /root/kidsmap-task33/docs/task33/qa21/browser.py --mode probe --output "$root" > "$evidence/launcher.log" 2>&1 &
launcher_pid=$!
finish() {
  if test -f "$root/browser-ready.json" && ! test -f "$root/run.json"; then
    curl --max-time 15 -fsS http://127.0.0.1:8781/finish >/dev/null || true
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
npx playwright-cli -s=qa21 snapshot > "$evidence/blank-snapshot.txt"
sed "s|__QA21_EVIDENCE__|$evidence|g" /root/kidsmap-task33/docs/task33/qa21/$payload.js > "$evidence/matrix.js"
npx playwright-cli -s=qa21 run-code --filename "$evidence/matrix.js" > "$evidence/matrix-cli.txt"
npx playwright-cli -s=qa21 snapshot > "$evidence/final-snapshot.txt"
finish
wait "$launcher_pid"
mkdir -p "$evidence/launcher"
cp -r "$root/." "$evidence/launcher/"
python3 /root/kidsmap-task33/docs/task33/qa21/summarize.py "$evidence"
