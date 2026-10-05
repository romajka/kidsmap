#!/bin/bash
set -euo pipefail
family=${1:?family}; stamp=${2:?stamp}
[[ "$family" =~ ^(r1|specialist|event|targeted|motion)$ && "$stamp" =~ ^[a-zA-Z0-9-]+$ ]]
mirror=/root/km28-browser
root=/tmp/task33-browser28-$family-$stamp
evidence=/root/task33-evidence/browser28-$family-$stamp
test ! -e "$root";test ! -e "$evidence";mkdir -p "$evidence"
cd /root/task33-browser-tools
export PATH=/root/task33-browser-tools/node_modules/.bin:$PATH
cp "$mirror/browser-source.json" "$evidence/source.json"
test -f "$mirror/docs/task33/final-audit/qa/browser_${family}_bridge/commands.py"
TASK33_BROWSER_FAMILY="$family" "$mirror/.venv/bin/python" "$mirror/docs/task33/final-audit/qa/browser_launcher.py" --mode probe --output "$root" > "$evidence/launcher.log" 2>&1 &
launcher_pid=$!
finish(){
 if test -f "$root/browser-ready.json" && ! test -f "$root/run.json";then curl --max-time 15 -fsS "http://127.0.0.1:8788/qa28/finish?token=$(basename "$root")" >/dev/null || true;fi
 wait "$launcher_pid" || true
 if test -f "$root/run.json";then mkdir -p "$evidence/launcher";cp -r "$root/." "$evidence/launcher/";fi
 npx playwright-cli -s=acceptance28 close > "$evidence/close-cli.txt" 2>&1 || true
}
trap finish EXIT
for i in $(seq 1 180);do
 test ! -f "$root/browser-ready.json" || break
 if ! kill -0 "$launcher_pid" 2>/dev/null;then cat "$evidence/launcher.log";exit 2;fi
 sleep 1
done
test -f "$root/browser-ready.json"
npx playwright-cli -s=acceptance28 open about:blank > "$evidence/open-cli.txt"
npx playwright-cli -s=acceptance28 snapshot > "$evidence/initial-snapshot.txt"
sed "s|__QA28_EVIDENCE__|$evidence|g" "$mirror/docs/task33/final-audit/qa/browser_${family}_matrix.js" > "$evidence/matrix.js"
npx playwright-cli -s=acceptance28 run-code --filename "$evidence/matrix.js" > "$evidence/result-cli.txt"
npx playwright-cli -s=acceptance28 snapshot > "$evidence/final-snapshot.txt"
npx playwright-cli -s=acceptance28 console error > "$evidence/console-cli.txt"
npx playwright-cli -s=acceptance28 requests > "$evidence/requests-cli.txt"
finish
wait "$launcher_pid"
"$mirror/.venv/bin/python" "$mirror/docs/task33/final-audit/qa/browser_source.py" current > "$evidence/source-current.json"
"$mirror/.venv/bin/python" "$mirror/docs/task33/final-audit/qa/browser_collect.py" "$evidence" "$family"
