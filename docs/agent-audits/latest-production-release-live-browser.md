# Production browser verification — 2026-09-15

Executed by the lead after confirming active application revision3aec046c. Real Chromium1228/Playwright, anonymous GET only. No production login, form submission or synthetic records.

Fresh page loads at390 and1280 for AZ/RU/EN: header visible; mobile drawer opens/closes; all three mobile language destinations match; desktop language dropdown opens. Zero JavaScript exceptions and observed HTTP400+ responses. Optional media, fonts and external integrations were blocked for the bounded six-case interaction probe. This is not a whole-page visual certification.

Separate focused probe allowed Google font assets and both actual site/admin hosts. RU desktop language dropdown works, fonts finish loading. RU and EN admin login each return200 in their explicit URL language with the opposite django_language cookie; the request headers confirm the conflicting cookie was actually sent to admin.kidsmap.az. No authentication was attempted.

Limit: RU home at1280 has document width1283 (3px overflow) in the font-enabled/media-blocked probe. Origin/baseline of this small overflow was not established; do not describe it as a verified regression or a fixed issue. The isolated admin list also retains its known390px overflow. Initial font-enabled navigation and sequential viewport-resize probes hit timeouts/element-stability waits; the final interactions below use fresh loads at each viewport. A separate fresh RU desktop probe sampled a stable button rectangle and clicked successfully.

Commands:

```sh
KIDSMAP_DEPLOYMENT_CONFIRMED=3aec046c node /tmp/kidsmap-latest-release/live-browser-app-only.cjs
node /tmp/kidsmap-latest-release/live-final-focus.cjs
```

Both final commands exited0. Structured observations:

```json
{
  "matrix": {
    "checks": [
      {
        "surface": "home",
        "lang": "az",
        "width": 390,
        "overflow": false,
        "status": 200
      },
      {
        "surface": "home",
        "lang": "az",
        "width": 1280,
        "overflow": false,
        "status": 200
      },
      {
        "surface": "home",
        "lang": "ru",
        "width": 390,
        "overflow": false,
        "status": 200
      },
      {
        "surface": "home",
        "lang": "ru",
        "width": 1280,
        "overflow": true,
        "status": 200
      },
      {
        "surface": "home",
        "lang": "en",
        "width": 390,
        "overflow": false,
        "status": 200
      },
      {
        "surface": "home",
        "lang": "en",
        "width": 1280,
        "overflow": false,
        "status": 200
      },
      {
        "surface": "admin-login",
        "lang": "ru",
        "cookie": "en",
        "status": 200
      },
      {
        "surface": "admin-login",
        "lang": "en",
        "cookie": "ru",
        "status": 200
      }
    ],
    "errors": [],
    "failed": [],
    "blocked": 179
  },
  "focused": [
    {
      "check": "ru-desktop-with-fonts",
      "ok": true,
      "width": 1280,
      "documentWidth": 1283,
      "fonts": "loaded"
    },
    {
      "check": "admin-cookie-conflict",
      "lang": "ru",
      "cookie": "en",
      "sent": true,
      "status": 200
    },
    {
      "check": "admin-cookie-conflict",
      "lang": "en",
      "cookie": "ru",
      "sent": true,
      "status": 200
    }
  ]
}
```
