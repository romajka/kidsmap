# Учёт переходов из AI-сервисов

KidsMap отправляет событие `ai_referral_visit` через существующий `gtag()` и
существующий endpoint `/events/track/`.

## Какие переходы распознаются

Основные источники:

- `chatgpt.com` → `chatgpt`;
- `perplexity.ai` → `perplexity`;
- `gemini.google.com` → `gemini`;
- `copilot.microsoft.com` → `copilot`;
- `claude.ai` → `claude`;
- `poe.com` → `poe`.

Дополнительно распознаются явно AI-ориентированные `deepseek`, `grok`,
`meta_ai`, `mistral`, `phind` и `youcom`.

Сначала проверяется `document.referrer`. Переходы с `kidsmap.az`, `www` и
поддоменов KidsMap считаются внутренними и игнорируются. Если referrer пуст,
используется только известное значение `utm_source`, например:

```text
https://kidsmap.az/ru/catalog/?utm_source=chatgpt
```

Неизвестный внешний referrer не считается AI referral. Обычная внутренняя
навигация не создаёт новое событие. Дополнительная защита в `sessionStorage`
не даёт повторно отправить тот же источник и landing path в одной вкладке.

## Состав события

Пример:

```json
{
  "event_type": "ai_referral_visit",
  "ai_source": "chatgpt",
  "landing_path": "/ru/catalog/",
  "page_type": "catalog",
  "language": "ru"
}
```

В событие не включаются referrer, полный URL, query string, UTM campaign,
email, телефон, пользователь или session key. Внутренняя запись создаётся
только при `LOCAL_ANALYTICS_STORAGE_ENABLED=1` и остаётся анонимной.

## Настройка GA4 для отчёта по `ai_source`

GA4 получает custom event и его параметры через `gtag("event", ...)`. Чтобы
параметр появился как измерение в отчётах:

1. Открыть нужную GA4 property.
2. Перейти **Admin → Data display → Custom definitions**.
3. Нажать **Create custom dimension**.
4. Заполнить:
   - Dimension name: `AI source`;
   - Scope: `Event`;
   - Event parameter: `ai_source`.
5. Сохранить. Имя параметра должно быть в точности `ai_source`.

При необходимости тем же способом создать event-scoped dimensions:

| Dimension name | Event parameter |
|---|---|
| AI landing path | `landing_path` |
| AI page type | `page_type` |
| AI page language | `language` |

Custom definitions начинают собирать данные после создания и не заполняют
старые события задним числом. Появление данных в стандартных отчётах может
занять 24–48 часов.

Официально: [GA4 custom events](https://developers.google.com/analytics/devguides/collection/ga4/events),
[event-scoped custom dimensions](https://support.google.com/analytics/answer/14239696).

## Exploration по AI-источникам

1. Открыть **Explore → Free form**.
2. Добавить dimensions:
   - `Event name`;
   - `AI source`;
   - при необходимости `AI landing path`, `AI page type`, `AI page language`.
3. Добавить metric `Event count`.
4. В Rows поставить `AI source`.
5. В Values поставить `Event count`.
6. Добавить фильтр:

   ```text
   Event name exactly matches ai_referral_visit
   ```

7. Для анализа конкретных входных страниц добавить `AI landing path` в Rows
   после `AI source`.

Для первичной проверки открыть **Reports → Realtime** и убедиться, что событие
`ai_referral_visit` поступило. Realtime подтверждает доставку, но полноценное
измерение `AI source` следует проверять после обработки данных GA4.
