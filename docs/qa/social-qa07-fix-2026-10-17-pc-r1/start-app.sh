#!/bin/sh
set -eu
qa=/mnt/c/kidsmap/.tmp/social07-pc-fix-r1
docker exec m09s07-fix-r1-app python "$qa/runtime.py" seed > "$qa/seed.log" 2>&1
docker exec -d m09s07-fix-r1-app sh -c 'python /mnt/c/kidsmap/.tmp/social07-pc-fix-r1/runtime.py serve > /mnt/c/kidsmap/.tmp/social07-pc-fix-r1/server.log 2>&1'
