# SPEC-QA-03 — мобильная навигация формы обрезана

Статус OPEN; P3; автор предложения и подтверждённый специалист. Current baseline failure, regression относительно другого commit не проверена. Среда fresh localhost:8814 WORKTREE HEAD `8d188b316f800fbedf0b1e376905dfd4924cb1b6`, 2026-10-10. Уверенность высокая.

URL: `/account/specialists/proposals/new/` и `/account/specialists/1/`, языковые варианты RU/AZ/EN.

1. Открыть одну из форм на360/390/768.
2. Посмотреть компактный блок «Шаг1 из5»; перейти нижней кнопкой к другому этапу.
3. Название текущего этапа и верхние стрелки обрезаны во всех трёх языках; desktop1024/1280/1440 показывает другой рабочий stepper.

Ожидание: название шага и стрелки целиком читаемы и доступны. Факт: header и nav высотой примерно8px с overflow:hidden; текст20px, стрелки32px. Повторно подтверждено18 из18 применимых сочетаний роль×язык×мобильная ширина. Документ не имеет горизонтального overflow: эта проверка сама по себе не обнаруживает внутреннюю обрезку.

Доказательства: [progress-recheck.result.txt](../progress-recheck.result.txt), [фрагмент](../screenshots/progress-recheck-person-ru-390.png), [полный экран](../screenshots/person-step-3-ru-390.png), [PC](../screenshots/person-step-3-ru-1440.png); остальные screenshots указаны в матрице.

Первопричина: `static/css/pages/specialists.css:917` селектор `.km-owner-mobile-progress div` назначает height8/overflow:hidden всем вложенным div, включая `.km-mobile-step-header` и `.km-mobile-step-nav`. Новые определения header/nav ниже не отменяют эти свойства. `owner_specialist_create.html:130–138` содержит новые вложенные div.

P3: обрезка затрудняет ориентацию и верхнюю навигацию длинной формы; нижние кнопки продолжают работать, подтверждённого блокирования отправки нет. Область — CSS конкретного мобильного stepper; зависимость — старое общее правило и новый markup, общие styles могут влиять на соседние формы, нужен ограниченный smoke.

Самостоятельный промпт:

```text
Прочитай AGENTS.md, .agents и docs/qa/module03-2026-10-10-r1/findings/SPEC-QA-03.md в фактическом корне KidsMap. Исправь только внутреннюю обрезку мобильной навигации формы специалистов. Сначала дай конкретный план; используй существующее согласование scope или согласуй его до реализации.
В author proposal и person editor RU/AZ/EN при360/390/768 header/nav имеют height8 и overflow:hidden, хотя текст20px и стрелки32px. Причина source-backed: старое правило .km-owner-mobile-progress div в static/css/pages/specialists.css:917 применяется к новым div header/nav. Сделай размеры заголовка и nav по содержимому, ограничь оформление8px полосой прогресса, сохрани кликабельность и видимый keyboard focus. Не расширяй изменение на редизайн всей формы. Перепроверь RU/AZ/EN ×360/390/768/1024/1280/1440: все5 этапов, длинный label, пустые/ошибочные состояния, Tab/Shift+Tab/Enter/Space, внутреннюю обрезку и реальные screenshots. Нужен rendered browser; scrollWidth<=viewport недостаточно. Сохрани нижние действия и desktop stepper. Только изолированный DJANGO_TESTING=1 и вымышленные данные; сохрани чужие изменения/стенды, без commit/push/deploy/production. Дай diff и свежую проверку, не правь existing assertions ради зелёного.
```
