# MOD-QA-07 — отдельное CSS-дополнение к сводке ошибок

**Новый scope, approval pending. CSS не применён. MOD07 целиком пока OPEN.** Предыдущая трёхфайловая правка завершена и повторного approval не требует.

Подтверждён тот же **MOD-QA-07**, дополнительная визуальная причина внутри его сводки. После устранения посимвольного HTML стало видно: `.km-error-banner` имеет `display:flex`, а h2 наследует крупный размер. На390px заголовок сжимается в узкую колонку и разбивается на множество строк, список стоит сбоку. Это не новое требование к backend/валидации и не повод менять assertions.

## Свежие доказательства

Actual RU/AZ/EN×390/1440:6cells/12observations, **3sourceFAIL на390 +3desktopcontrolsPASS**. CSS feasibility через временный `page.addStyleTag` — отдельно **6SIMULATED PASS**, не sourceGREEN. [Raw](native-layout-plan.js.result.json), layout-before/candidate PNG и размеры в [manifest](png-manifest.json). Persisted domain/M2M/locations/documents unchanged,0local diagnostics. Исходный CSS SHA256 остаётся entryhash, candidateappliedfalse. Визуально просмотрены RU390actual/candidate.

## Один точный файл

**`static/admin/css/pages/specialist_form.css`**, добавить только2scopedrules в конец:

```css
/* Specialist server error summary contains a heading and a message list. */
.km-specialist-form-page [data-specialist-errors] {
  display: block;
}
.km-specialist-form-page [data-specialist-errors] > h2 {
  margin: 0 0 8px;
  font-size: 1rem;
  line-height: 1.4;
}
```

[Exact diff](css-supplement.diff), [source/candidate SHA256](css-supplement-manifest.json), [candidate only](candidate-css.css). Кореньстраницы+dataattribute ограничивают правила одной specialist summary; другие banner/form/page/header не затрагиваются. Меняется расположение заголовка/списка и размер заголовка, текст/ссылки/валидация/JS/CSSобщихэкранов не меняются. Новых PO/backendtests/dependencies не нужно.

## Выполнение после отдельного approval

1. Snapshot текущегоroot/HEAD/branch/dirty/active_run/foreignprocesses/containers/sourcehash. Проверить принадлежность и актуальность собственного profile, fictionaldata/DB/cache/media/private-media/email и blockedegress. Не трогать чужие стенды. Новый QA CSSfixrun, свежие isolatedRU/AZ/ENlocales verifybeforedjango.setup/soleLOCALE_PATHS, текущий ownprocess source.
2. Сверить css-supplement sourcehash и сохранить current core/test hashes. Использовать свежий подтверждённый sourceRED выше; если process/source drift — повторить только один failingmobilecase. Применить только этот один CSSfile.
3. **Targeted nativeGREEN** RU/AZ/EN×360/390/768/1024/1280/1440: actualSaveinvalid→oneerror, заголовок не более2читаемых строк, список ниже, безhorizontalclip/перекрытия, сообщение1целое, link→visiblecheckboxfocus, сохранностьввода. Representative multiple/inlinecases толькоRU390/EN1440, чтобы проверить длинный список; не повторять неизменённую полную MOD07JS/backendматрицу.
4. **Не повторять5backendmethods и весь184checks корпус:** сохранить completedPASS при sourcehashmatch2approvedappfiles/newtest/остальныхзависимостей. NewCSS browseracceptance — отдельное evidence, assertions не ослаблять. Если новая причина вне CSS — отдельноPLAN.
5. Source/locale/domainbefore-after, exactcommands/exits/counts, console/network/PNGmanifest иpreservation. Нетsuccessfulsave/delete/production. После реальногоCSSGREEN закрыть MOD07 в проверенномscope. MOD08отдельныйPLAN, полныйmodule08одинразпосле08; globalотдельно; module09/commit/push/deployнеразрешены.

Риск минимален: новый специфичный селектор переопределяетflexтолькоу данногоerrorbanner. Обычныйwrapприоченьдлинномсловедопустим, но текущиеRU/AZ/ENtitles должныумещаться. Candidatefeasibility уже показываеткомпактную сводку без изменениякаких-либоданных. Применение/реальныйCSSGREENпокаNOTRUN.

Основание отдельного approval: текущий одобренный IMPLEMENTATION_PLAN.md прямо исключал CSS изscope; userправило требует отдельно согласовывать существенное расширение/новуюпричину. Повторное согласование уже применённых3файлов не запрашивается.
