#!/bin/sh
set -eu
qa=/mnt/c/kidsmap/.tmp/module09-full-pc-r1
for role in guest author owner employee moderator staff admin empty; do
 python3 "$qa/run_browser.py" matrix "$role"
done
