# ORG-QA-04 — необходимое дополнение RU fallback

2026-10-13, текущий checkout `/home/ramin/kidsmap`, branch task33-progress, HEAD e4e05cc213b34e2d771ecb854901bfd016d1db51 +approved dirty WORKTREE. IMPLEMENTATION NOT RUN этого дополнения.

Свежий `copy-proof.json` после согласованного AZ/EN patch доказывает: RU section/model/badge теперь возвращают AZ («Adlar», «Təşkilatlar», «Sahiblik»). `LANGUAGE_CODE='az'` — default catalogue fallback. В RU PO нет14 новых exact msgid, поэтому добавление AZ translations изменило прежний RU fallback. Это regression того же ORG-QA-04, не новый finding/редизайн.

Необходимое расширение: единственный дополнительный файл `locale/ru/LC_MESSAGES/django.po`. Добавить ровно14 отсутствующих entries из `../module02-remaining-recheck-2026-10-13-r1/proposed-copy.json`, исключая «Одобрить заявку» (RU перевод уже есть). Для каждого `msgstr` равен исходной русской подписи `msgid`. Другие строки/headers/fuzzy/PO не менять. Backend/settings/LANGUAGE_CODE менять не нужно.

После отдельного approval: внести эти14 entries, собрать новые fresh RU/AZ/EN manifests для собственных profiles; старые/shared MO не перезаписывать; перезапускать только свои fixes/full profile после точного cmdline readback. Проверить actual gettext + lazy labels RU→AZ→EN→RU, native admin language dropdown и affected editor/browser states. Полный module02 test run один раз после всех locale corrections. Existing assertions unchanged. ORG-QA-04 пока OPEN, полный module02 PASS не заявляется.

No commit/push/deploy/production, чужой WORKTREE/active_run/стенды сохранить.
