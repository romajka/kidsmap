# SITE-QA-01 — Staff без model permissions меняет глобальный логотип

**OPEN / P1 / LOCAL C:\kidsmap / module10-2026-10-10-r1 / 2026-10-10.** Классификация: pre-existing LOCAL WORKTREE security failure. Execution: /root sequential, свежие native Chromium и own isolated DB. Production UNKNOWN. Исполнитель аудита не менял application sources/существующие assertions; чужой drift зафиксирован в [SOURCE-DRIFT](../SOURCE-DRIFT.md).

**Роль:** staff без permissions/groups. **URL/endpoint:** `/admin/catalog/sitegalleryimage/; /admin/catalog/sitegalleryimage/ajax-upload/; /admin/catalog/sitegalleryimage/ajax-delete-main-image/`.

**Шаги:** Войти как qa10_staff (is_staff=True, is_superuser=False, permissions/groups=0). Открыть медиахаб. В собственном браузерном контексте отправить multipart POST field=logo с валидным CSRF. Проверить DB и публичную главную. Отправить delete POST с валидным CSRF.

**Ожидание:** 403 и неизменные файлы/настройки при отсутствии model permission.

**Факт:** GET/оба POST возвращают 200; новый файл появляется на публичной главной, затем удаляется. Без CSRF получено 403. Админ восстановил вымышленный логотип через UI.

**Перепроверка WORKTREE:** Supplemental native process8825/8826 started from current-snapshot.json after recorded foreign source drift. Module10 relevant handlers/templates/MO remain unchanged; own reports preserve entry evidence. SITE-QA-01 current recheck is GET only; upload/delete proof earlier, identical handler hashes, no new security mutation.

**Приоритет и эффект:** P1: любой активный staff может менять глобальный публичный бренд. Production exploitation не проверялся.

**Первопричина / гипотеза:** Подтверждено: custom changelist_view обходит super при отсутствии placement; AJAX handlers не проверяют has_change_permission. admin_site.admin_view допускает активный staff, но не добавляет model-level authorization.

**Source:** `src/catalog/domain_admin/site.py:570`; `src/catalog/domain_admin/site.py:975`; `src/catalog/domain_admin/site.py:986`; `src/catalog/domain_admin/site.py:1065`. Source refs — объяснение, rendered evidence перечислено ниже. Confidence: высокий для наблюдаемого эффекта; confidence root указан отдельно.

**Доказательства:**

- [acl.result.txt](../acl.result.txt)
- [acl-identity.json](../acl-identity.json)
- [screenshots/acl-media-page-staff.png](../screenshots/acl-media-page-staff.png)
- [screenshots/acl-public-logo-staff.png](../screenshots/acl-public-logo-staff.png)
- [screenshots/acl-native-restored.png](../screenshots/acl-native-restored.png)
- [current-boundary.result.txt](../current-boundary.result.txt)

**Область исправления:** Model permissions для медиахаба, upload/delete и соответствующих SiteSettings/SiteGalleryImage полей; валидный staff с ограниченным доступом должен получать 403. Не расширять разрешения всем staff.

**Владелец / зависимости:** Canonical Django/security roles; проверить чтение медиахаба отдельно от изменения, CSRF и штатный superuser workflow.

**Следующий шаг:** отдельный repair scope с конкретным планом. [Готовый самостоятельный промпт](SITE-QA-01-repair.txt). Аудит ничего не исправляет.
