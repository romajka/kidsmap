# Команды и воспроизводимость

Рабочий snapshot и точные SHA: source-entry.json, source-applied.json, source-final.json. Shell PowerShell → WSL Ubuntu-24.04; скрипты этого пакета запускались Python3 из `/mnt/c/kidsmap/docs/qa/site-qa21-fix-2026-10-18-pc-r1/`. Собственные временные конфигурации и сырые test/server logs находятся в игнорируемом `.tmp/site21-pc-fix-r1`; production не используется.

Порядок: prepare_bootstrap.py → bootstrap.py → prepare_runtime.py → run_red_setup.py → readonly browser-width-diagnostic → prepare_stable_native.py → run_native_phase.py stable RED → apply_candidate.py → run_green_setup.py и run_backend.py → static_probe.py → prepare_extended_checks.py → run_extended_native.py → finalize.py. Скрипты создания/применения ресурсов не предназначены для слепого повторного запуска; их guards и identity proofs сохранены. Первый bootstrap race и initial RED retained отдельно.

Точные argv/exit для запуска профиля и native suites: evidence/*commands*.json, evidence/browser-commands.jsonl, evidence/*-cli.txt. Playwright CLI через npx node@24 и @playwright/cli, собственный именованный browser profile; browser_driver.py и browser-*.js сохранены целиком. Assertions выполняются по реальным локальным страницам и синтетической fixture.

Серверные регрессии, exit0:

```text
docker exec m10s21-fix-r1-app python /mnt/c/kidsmap/.tmp/site21-pc-fix-r1/runtime.py test catalog.testcases.test_site_qa19_catalog_content catalog.testcases.public.TestCatalogContentSettingsWiring catalog.testcases.test_site_qa06_media_validation catalog.testcases.test_site_qa01_media_permissions catalog.testcases.test_site_qa15_settings_concurrency catalog.testcases.admin.TestSiteGalleryImageAdminMedia catalog.testcases.admin.TestAdminSidebarStructure catalog.testcases.test_public_section_switches
```

105 tests /50.338s /OK. Доказательство разделения normal/test storage — evidence/test-isolation.json; список105 уникальных методов и origin/compile — evidence/static-runtime.json.

Финальные безопасные проверки: Windows Git `diff --check`, WSL Git `apply --reverse --check implemented.diff`; source SHA, refs/index, старые артефакты и контейнеры; локальный readonly fixture state. Полные команды/проверки приведены в finalize.py, выходы — evidence/final-checks.json. Финальная сумма пакета не включает сам artifact-manifest.json.
