# Moderation return release — 2026-11-16

Authorized: push and deploy the completed place moderation-return improvements.
16 runtime files plus regression tests; no migrations or content decisions.
Existing unrelated photo-editor and notification redesign work is excluded. The current production notification template already displays reasons without a false success icon.

The release overlays only manifest-bound files onto the verified live image,
retaining the previously deployed analytics patch. prepare captures private runtime
configuration, verifies round-trip equivalence, backs up static and PostgreSQL,
restores the database to a disposable no-network instance, builds an isolated
allowlisted context, and checks sources, migrations, templates and analytics boundaries.
activate replaces only web, checks health, all source/static hashes, localized public
pages, and unchanged configuration/database/Redis identities. On failure it restores
the previous image and static files. No migrations are applied.

Server artifacts: /opt/kidsmap-releases/20261116-moderation-return (root-only).
release_revision.txt is supplied from the exact committed release checkout.
Do not replay this recipe on a different baseline.
