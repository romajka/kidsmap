#!/bin/bash
# Fresh prior-stage evidence against the root-frozen shared source mirror.
set -euo pipefail
cd /root/task33-browser-tools
export PATH=/root/task33-browser-tools/node_modules/.bin:$PATH
stage=${1:?21 or 22 required}
stamp=${2:?Unique stamp required}
payload=${3:-matrix}
[[ "$stage" == 21 || "$stage" == 22 ]]
[[ "$stamp" =~ ^[a-zA-Z0-9-]+$ ]]
if [[ "$stage" == 21 ]];then
 npx playwright-cli -s=qa21 open about:blank >/tmp/task33-qa21-open-$stamp.txt
 /bin/bash /mnt/c/kidsmap/docs/task33/qa21/run-browser.sh "$stamp" "$payload"
else
 npx playwright-cli -s=qa22 open about:blank >/tmp/task33-qa22-open-$stamp.txt
 /bin/bash /mnt/c/kidsmap/docs/task33/qa22/run-browser.sh "$stamp" "$payload"
fi
