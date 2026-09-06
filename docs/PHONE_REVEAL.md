# Public place contacts

Public cards, detail pages, map payloads and place SEO do not embed structured phone numbers. POST `place_phone_reveal` returns callable contacts after a click. Site support contacts and authenticated owner editing are unaffected.

The endpoint requires CSRF, filters inactive/deleted/unpublished places, sends no-store responses, and limits requests to 30 per minute per connection IP using the shared Django cache (Redis in production). Changing sessions does not reset the limit. This prevents simple page scraping; it does not make contact data inaccessible to a bot capable of interacting with the site.

## Deployment

Set `PHONE_REVEAL_TRUSTED_PROXIES` to the exact source IP address(es) of your Nginx proxy as seen by Django, comma separated. Nginx in `deploy/nginx/kidsmap.az.conf` already overwrites `X-Real-IP`. Only explicitly trusted connections may supply that header. Do not use arbitrary client addresses or trust all forwarded headers. Without this setting, visitors behind a reverse proxy share its connection-IP limit. `PHONE_REVEAL_RATE_LIMIT` changes the per-minute limit (default 30).

Deploy templates and static assets together and invalidate previously cached public HTML/map responses containing phone data. Run collectstatic using the normal deployment process.

## Verification

`python manage.py test catalog.testcases.phone_reveal --noinput`

DOM interaction tests: `npm install --prefix .tmp/phone-dom --no-save --package-lock=false jsdom`, then `node --test scripts/test_phone_reveal.cjs`.

Browser visual verification remains necessary on mobile and desktop; browser automation was unavailable in the implementation environment.
