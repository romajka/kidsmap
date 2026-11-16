# Five fixes: audited overlay transition

The live image `sha256:f351ed0a3665a3862306ff80890ed113456749f98a9ef0b1aa3366e47df5d5bc`
is labelled `66badd5370a0dc183c4884eae229890aca67b4c1`. A read-only comparison of
3,411 tracked source files found exactly nine differences: three already released
analytics files and six release/test files absent from the earlier overlay image.
`baseline-drift.json` records their Git blob hashes, including explicit absence.

This release commits the three live analytics files byte-for-byte and includes
their regression tests. `transition.py` accepts only the audited image, revision,
and complete difference set, and refuses a candidate that drops any analytics
file. Every other baseline file is verified by the ordinary runner. Preparation
also verifies every tracked source file in the full candidate image without a
network or database. Post-activation verification requires ordinary source parity.

Extract the exact tested commit, then run its recipe with the normal installation
root and exact current main SHA:

```sh
python3 /path/to/extracted/scripts/releases/five-fixes-20261116/transition.py --root /opt/kidsmap <tested-main-SHA>
```

All ordinary guards remain: release lock, clean checkout, main revision, Compose
config hash/round-trip, immutable rollback image, runtime fingerprint, static
backup, read-only checks, pending-migration refusal, journal and automatic recovery.
No migration, database restoration, content decision or environment change occurs.
Future releases use `scripts/deploy-server.sh`; the ordinary overlay guard is unchanged.
