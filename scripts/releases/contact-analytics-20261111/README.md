# Contact analytics, 2026-11-11

Approved scope: activate the GA4 public-host filter and release exactly the three
runtime files in `manifest.json`. The filter is ACTIVE. No content, schema,
credentials, proxy, outbox or unrelated local UI changes belong to this release.

The inspected production baseline is commit
`3fabfdcc456a6592d3091ce62b46e9f958ea6468`, image
`sha256:457fc647e23f3a2e262ee3a13e609b7452dc0faa022cc007fd51b4f4899666f4`.
All three production source files match that commit byte for byte. `source.patch`
is the entire application change; `manifest.json` binds its before/after bytes.
The build context contains only the overlay, Dockerfile and ignore rules.

`release.py prepare` runs on the server only. It refuses baseline drift, captures
the effective compose configuration privately, preserves the old image and full
static tree, takes a PostgreSQL dump and restores it into a disposable container
without network access. It builds an overlay from the running image and runs
system checks, migration checks and the collection-boundary probe. It never
applies migrations. Logs and rollback data stay under the root-only directory
`/opt/kidsmap-releases/20261111-contact-analytics`.

`release.py activate` rechecks the baseline, collects static without clearing and
replaces only web. It checks health, source hashes, public HTML/static bytes,
collection boundaries, unchanged environment/mounts/ports and unchanged database
and Redis containers. Failure restores the old static tree and web image.
`release.py rollback` provides the same bounded recovery explicitly.

Local validation: 40 Django and 19 Node tests passed; six earlier instrumented
browser scenarios cover AZ/RU/EN card/detail contacts. No synthetic production
analytics events, real telephone calls or WhatsApp messages are sent by probes.

Do not replay this dated release against another baseline or use a generic
deployment script. Never copy server compose snapshots, database dumps or logs
into the repository. Deployment status is recorded in the dated audit report.
