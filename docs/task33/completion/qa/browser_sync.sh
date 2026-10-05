#!/bin/bash
set -euo pipefail
mirror=/root/km-completion-browser
artifact=/mnt/c/kidsmap
mkdir -p "$mirror"
for name in src templates static locale config scripts; do
 mkdir -p "$mirror/$name"
 rsync -a --delete --exclude=__pycache__ --exclude='*.pyc' "$artifact/$name/" "$mirror/$name/"
done
mkdir -p "$mirror/docs/task33/qa04" "$mirror/docs/task33/completion/qa"
rsync -a --exclude=__pycache__ /mnt/c/kidsmap/docs/task33/qa04/ "$mirror/docs/task33/qa04/"
rsync -a --include='browser*/***' --include='browser*' --exclude='*' /mnt/c/kidsmap/docs/task33/completion/qa/ "$mirror/docs/task33/completion/qa/"
cp "$artifact/manage.py" "$mirror/"
test -e "$mirror/.venv" || ln -s /root/km24-security/.venv "$mirror/.venv"
find "$mirror/locale" -name django.po -print0 | while IFS= read -r -d '' po; do msgfmt "$po" -o "${po%.po}.mo"; done
"$mirror/.venv/bin/python" "$mirror/docs/task33/completion/qa/browser_source.py" freeze
