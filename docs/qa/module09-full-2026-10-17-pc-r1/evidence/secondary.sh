#!/bin/sh
set -eu
qa=/mnt/c/kidsmap/.tmp/module09-full-pc-r1
python3 "$qa/secondary_driver.py" open http://127.0.0.1:33380/ru/reviews/ --config="$qa/playwright.json"
for role in moderator staff admin empty; do
 python3 "$qa/secondary.py" "$role"
done
