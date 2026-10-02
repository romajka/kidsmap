# Stage05 isolated migration generation

`python3 docs/task33/qa05/generate.py --mode probe --output /tmp/NEW_EMPTY_DIRECTORY`

Loads unchanged qa04/run.py. Child environment prepends this directory solely to select qa05/commands.py; settings/guards/safety tests stay QA04. The command generates catalog migration named task33_catalog_structure in the working tree. It may modify/create a local migration, so use only when schema changes require it; it never applies to a persistent database. Same nonce-owned, network-none, no-port PostgreSQL/tmpfs/Unix socket and finally cleanup. No environment inheritance, installation, credentials, public services or production commands.

Verification uses the original runner:

`python3 docs/task33/qa04/run.py --mode all --label catalog.testcases.test_task33_catalog_schema --output /tmp/NEW_EMPTY_DIRECTORY`

Raw logs remain /tmp. Keep only aggregate results/test identities/commands/source hashes in reports. Migration reverse in the compatibility test happens only in the disposable test database; it is not a release rollback procedure.
