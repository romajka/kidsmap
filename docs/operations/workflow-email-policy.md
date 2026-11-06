# Service email delivery

Service inbox events and authentication emails are separate. This policy affects
`EmailOutbox` only; registration, password reset, email change, account deletion,
staff promotion requests and staff offboarding requests keep their existing paths.

## Delivery rules

* Ownership transfer and access removal: immediate, one current event per email.
* Invitations, relationship confirmations, moderation decisions and results:
  collect until 15 minutes after the latest eligible event, with a one-hour maximum
  wait during a continuous stream. At most one digest per mailbox every 30 minutes.
* Ordinary events expire after 24 hours; security events after seven days. Current
  entity state, recipient mailbox/rights and event version are checked again on retries.
* Staff do not receive ordinary email for their own actions. Their inbox is preserved.
* Digests include counts and up to ten decision titles; private moderator comments
  remain in the authenticated inbox. Current status and next steps are linked there.
* All workers serialize on a hashed mailbox key before claiming its outbox rows.
  Up to 1,000 intents enter a digest; additional events remain subject to cooldown.
* SMTP failures retry with 2, 4, 8 and 16 minute delays, then fail on attempt five.
  SMTP acceptance followed by an application crash can still cause one repeated
  email: the SMTP/DB boundary is at least once, not exactly once.

## Operations

Run these commands inside the web container.

The database policy defaults to disabled even if an old scheduler still invokes
the command. `deliver_workflow_outbox` defaults to a read-only preview and
requires `--send` for actual delivery. Preview includes aggregate suppression
reasons, without recipient addresses or private event content.

```sh
python manage.py workflow_email_policy
python manage.py deliver_workflow_outbox
python manage.py workflow_email_policy --enable
python manage.py deliver_workflow_outbox --send --limit 50
python manage.py workflow_email_policy --disable
```

Enabling sets a fresh cutoff: earlier pending events are suppressed, never replayed.
An already enabled policy is unchanged by repeated `--enable`. Re-enabling after
disable starts a new cutoff and deliberately does not catch up on the held queue.
Sent rows and inbox history are never changed. `sent`, `retry`, `failed` count email
batches; `notifications_sent` and `suppressed` count underlying event intents.
The limit is SMTP batches per invocation; previews describe the queue without that limit.

Keep the two-minute scheduler paused during deployment. Apply migration 0154,
verify the deployed revision, preview, activate the cutoff, then enable the scheduler.
Do not generate production emails for testing. Use the isolated PostgreSQL suite
and LocMem/acceptance-ledger backends for the 175-event and crash regressions.

Rollback: disable the policy and scheduler first, restore the previous web image
and static archive. Keep the additive policy/state tables and delivery history;
do not restore an older database snapshot over new business activity.
