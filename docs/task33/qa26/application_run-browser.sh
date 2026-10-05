#!/bin/bash
set -euo pipefail
stamp=${1:?Unique stamp required}
[[ "$stamp" =~ ^[a-zA-Z0-9-]+$ ]]
mirror=/root/km26-browser-frozen
root=/tmp/task33-browser26-$stamp
evidence=/root/task33-evidence/browser26-$stamp
test ! -e "$root"
test ! -e "$evidence"
mkdir -p "$evidence"
cd /root/task33-browser-tools
export PATH=/root/task33-browser-tools/node_modules/.bin:$PATH
test -f "$mirror/docs/task33/qa26/application_bridge/commands.py"
cp "$mirror/browser-source-sha256.json" "$evidence/source-sha256.json"
test -f /root/task33-browser-tools/material22.css
test -f /root/task33-browser-tools/material.ttf
"$mirror/.venv/bin/python" "$mirror/docs/task33/qa26/application_browser.py" --mode probe --output "$root" > "$evidence/launcher.log" 2>&1 &
launcher_pid=$!
finish() {
 if test -f "$root/browser-ready.json" && ! test -f "$root/run.json"; then
  curl --max-time 15 -fsS "http://127.0.0.1:8786/qa26/finish?token=$(basename "$root")" >/dev/null || true
 fi
 wait "$launcher_pid" || true
 if test -f "$root/run.json"; then mkdir -p "$evidence/launcher";cp -r "$root/." "$evidence/launcher/";fi
 npx playwright-cli -s=application26 close > "$evidence/close-cli.txt" 2>&1 || true
}
trap finish EXIT
for i in $(seq 1 180); do
 if test -f "$root/browser-ready.json";then break;fi
 if ! kill -0 "$launcher_pid" 2>/dev/null;then cat "$evidence/launcher.log";exit 2;fi
 sleep 1
done
test -f "$root/browser-ready.json"
npx playwright-cli -s=application26 open about:blank > "$evidence/open-cli.txt"
npx playwright-cli -s=application26 snapshot > "$evidence/initial-snapshot.txt"
matrix=${2:-$mirror/docs/task33/qa26/application_matrix.js}
sed "s|__QA26_EVIDENCE__|$evidence|g" "$matrix" > "$evidence/matrix.js"
npx playwright-cli -s=application26 run-code --filename "$evidence/matrix.js" > "$evidence/result-cli.txt"
npx playwright-cli -s=application26 snapshot > "$evidence/final-snapshot.txt"
npx playwright-cli -s=application26 console error > "$evidence/console-cli.txt"
npx playwright-cli -s=application26 requests > "$evidence/requests-cli.txt"
finish
wait "$launcher_pid"
case "$(basename "$matrix")" in
 application_clock_causal.js) collector=application_clock_collect.py ;;
 application_diagnostics.js) collector=application_diagnostic_collect.py ;;
 application_runtime_css.js) collector=application_runtime_collect.py ;;
 *) collector=application_collect.py ;;
esac
"$mirror/.venv/bin/python" "$mirror/docs/task33/qa26/$collector" "$evidence" > "$evidence/summary.json"
