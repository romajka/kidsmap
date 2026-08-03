# Подтверждение KidsMap в Google и Bing

Код KidsMap готов к HTML meta verification, но реальные значения нельзя
добавлять в git. Они хранятся только в `/opt/kidsmap/.env`.

## Google Search Console: рекомендуемый Domain property

1. Открыть [Google Search Console](https://search.google.com/search-console/).
2. Выбрать **Add property → Domain**.
3. Ввести только `kidsmap.az` — без `https://`, `www` и пути.
4. Google покажет точное значение DNS TXT. Не закрывать окно и не изменять
   значение.
5. Добавить этот TXT у DNS-провайдера для корня домена. Имя записи обычно `@`,
   но использовать нужно формат, который показывает конкретный DNS-провайдер.
6. Дождаться распространения DNS и нажать **Verify**.

Domain property включает HTTP/HTTPS и все поддомены, включая `www` и `admin`.
Google разрешает подтверждать Domain property только через DNS. Без отдельного
разрешения DNS не менять.

Официально: [типы properties](https://support.google.com/webmasters/answer/34592),
[проверка владения](https://support.google.com/webmasters/answer/9008080).

## Google: подтверждение через meta tag

Meta tag работает для **URL-prefix property**, а не для Domain property:

1. Добавить property `https://kidsmap.az/`.
2. Выбрать метод **HTML tag**.
3. Google покажет тег вида:

   ```html
   <meta name="google-site-verification" content="ЗНАЧЕНИЕ_ОТ_GOOGLE" />
   ```

4. Скопировать только значение атрибута `content`, без HTML, кавычек и имени
   тега.
5. Записать его на сервере в `/opt/kidsmap/.env`:

   ```dotenv
   GOOGLE_SITE_VERIFICATION=ЗНАЧЕНИЕ_ОТ_GOOGLE
   ```

6. После разрешённого деплоя проверить исходный HTML:

   ```bash
   curl -fsS https://kidsmap.az/ | grep 'google-site-verification'
   ```

7. Нажать **Verify** в Search Console. После подтверждения тег не удалять:
   Google периодически перепроверяет владение.

## Bing Webmaster Tools

1. Открыть [Bing Webmaster Tools](https://www.bing.com/webmasters/).
2. Лучший быстрый вариант после подтверждения Google — **Import from Google
   Search Console**. Bing импортирует подтверждённый сайт и sitemap после выдачи
   разрешения.
3. Для ручного добавления указать `https://kidsmap.az/`.
4. Выбрать **Meta tag authentication** и скопировать только значение `content`
   из тега:

   ```html
   <meta name="msvalidate.01" content="ЗНАЧЕНИЕ_ОТ_BING" />
   ```

5. Записать значение в `/opt/kidsmap/.env`:

   ```dotenv
   BING_SITE_VERIFICATION=ЗНАЧЕНИЕ_ОТ_BING
   ```

6. После разрешённого деплоя проверить:

   ```bash
   curl -fsS https://kidsmap.az/ | grep 'msvalidate.01'
   ```

7. Нажать **Verify** в Bing.

Bing также поддерживает DNS/CNAME и XML-файл. Не создавать записи или файлы,
пока Bing не покажет точное значение для выбранного сайта.

Официально: [добавление и подтверждение сайта](https://www.bing.com/webmasters/help/add-and-verify-site-12184f8b).

## Отправка sitemap

Перед отправкой проверить публичный URL:

```bash
curl -fsSI https://kidsmap.az/sitemap.xml
```

Использовать один адрес:

```text
https://kidsmap.az/sitemap.xml
```

В Google: выбрать property → **Sitemaps** → вставить `sitemap.xml` → **Submit**.

В Bing: выбрать сайт → **Sitemaps → Submit sitemaps** → вставить полный URL.

Официально: [Google Sitemaps report](https://support.google.com/webmasters/answer/7451001),
[Bing Sitemaps](https://www.bing.com/webmasters/help/sitemaps-3b5cf6ed).

## Проверка IndexNow

1. Убедиться, что `INDEXNOW_KEY` задан только в server `.env`.
2. Проверить key-файл, подставив реальное значение:

   ```bash
   curl -fsS https://kidsmap.az/ЗНАЧЕНИЕ_INDEXNOW_KEY.txt
   ```

3. Посмотреть пакет без отправки:

   ```bash
   docker compose exec -T web python manage.py submit_indexnow --dry-run
   ```

4. После отдельного разрешения отправить один URL:

   ```bash
   docker compose exec -T web python manage.py submit_indexnow --limit 1 --force
   ```

5. В Bing открыть выбранный сайт → **IndexNow** и проверить появление отправки.
   Ответ API `200` или первый ответ `202` означает приём уведомления, но не
   гарантирует индексацию страницы.

Официально: [IndexNow](https://www.indexnow.org/documentation),
[проверка активности в Bing](https://www.bing.com/webmasters/help/URL-Submission-62f2860b).
