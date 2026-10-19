# ADJ-ACTIVITY-TITLE — existing OPEN/P3, outside SOCIAL05

В изолированном fixture Activity имеет name_az/name_ru/name_en=Fictional shared activity, но typed review page h1 показывает Activity object (1). Воспроизводится RU/AZ/EN×390/768/1440:9heading assertions FAIL, остальные54checks этих9cells PASS; source CSS selector .site-reviews-page здесь не matches.

Evidence: [shared.json](shared.json), [shared-cli.txt](shared-cli.txt), [SIMULATED original-CSS parity](shared_baseline.json),9baseline PNG в [manifest](png-manifest.json). После удаления только approved hunk из asset response в браузере original normalized CSS SHA=ded551a9444ce50acfa4408a8c4a60072515353ed12d3158412d2f5576d38158; те же9заголовков. Это контроль baseline, не application rollback. Исходные9FAIL сохранены без изменения assertions.

src/catalog/controllers/typed_reviews.py:98 задаёт target_name через getattr(target,'name_i18n',None) or str(target). Activity в src/catalog/models/catalog_structure.py:132 хранит localized name fields; observed fallback даёт стандартную model string. Оба файла совпадают с pre-SOCIAL05 source hashes. Graph search нашёл Activity, coverage metadata_changed/unavailable; relevant source прочитан. Наличие имени в fixture подтверждено seed source.

Влияние: пользователь видит техническую model label вместо названия направления на странице отзывов. Предлагается отдельный read-only PLAN с проверкой canonical localized Activity name resolver и его consumers; сначала согласовать точный scope. App fix/test/PR/deploy здесь NOT RUN. SOCIAL05 не расширялся; module09/global acceptance не заявлены.
