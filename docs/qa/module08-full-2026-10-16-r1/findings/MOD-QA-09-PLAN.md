# PLAN MOD-QA-09 — fuzzy-переводы счётчика и метаданных очереди

Новый finding внутри модуля08, не запуск модуля09. P3: в AZ/EN строка «Найдено … карточек» остаётся русской. Количество/фильтрация верны. В обоих PO запись fuzzy, устаревший msgstr использует total вместо текущего count; fresh compiler правильно исключает её. Это существующая отдельная причина, вне одобренного MOD08 renderer scope.

Дополнительно тот же fuzzy-defect у msgid «создано»: существующие AZ Yaradılıb/EN Created корректны, но исключены compiler из-за fuzzy. Подтверждение отдельно в created-label-recheck.js.result.json/PNG.

Точный предлагаемый scope3files:
- locale/az/LC_MESSAGES/django.po: только запись msgid «Найдено %(count)s карточек», снять fuzzy, перевести «%(count)s kart tapıldı», сохранить count.
- locale/en/LC_MESSAGES/django.po: та же запись, «Listings found: %(count)s», снять fuzzy; формат работает при0/1/нескольких.
- В тех же2PO также снять только fuzzy у msgid «создано», сохранив уже правильные msgstr; иных ключей не менять.
- NEW src/catalog/testcases/test_mod_filter_count_localization.py: actual authenticated Place/Event/Specialist drawer counts0/1/2 в AZ/EN; q/count правильны, перевод не fallbackRU. Targeted RED→GREEN при fresh own RU/AZ/EN MO. Отдельный actual Place metadata guard на локализованное «создано». Existing assertions не менять.

[Reviewable two-PO diff](MOD-QA-09-proposed.diff), [SHA/unapplied manifest](MOD-QA-09-manifest.json). Application/PO не изменены. JS/CSS/backend/filter semantics/RU copy вне scope.

После approval: только новая группа +один общий renderer count guard; native AZ/EN×3queues×360/1440,0/1/2results, select/Reset/visible footer and PNG; RU representative; новые own locales до setup иsource/MO/domain/preservation gate. Сохранить результаты уже выполненного полного ACCEPT-08; весь неизменённый корпус повторно не запускать. Новая причина — отдельное согласование.
