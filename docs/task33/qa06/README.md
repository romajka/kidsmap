# Stage06 isolated verification

Reuse unchanged QA04 runner/guards; fresh PostgreSQL container, network none, no ports, Unix socket only, clean environment with DJANGO_TESTING=1, private cache/media/locmem email. Never invoke manage.py using the project environment.

Targeted contracts:

```sh
python3 docs/task33/qa04/run.py --mode all --label catalog.testcases.test_task33_ownership --label catalog.testcases.test_task33_catalog_schema --output /tmp/unique-empty-stage06-target
```

Full canonical discovery:

```sh
python3 docs/task33/qa04/run.py --mode all --output /tmp/unique-empty-stage06-full
```

Generated additive migration0118 using only the owned disposable database:

```sh
python3 docs/task33/qa06/generate.py --mode all --output /tmp/unique-empty-stage06-generate
```

Generation wrapper supplies its `commands.py` through clean PYTHONPATH; original QA04/QA05 files remain unchanged. Raw logs stay in /tmp. Completion requires suite-results.json AND run.json (child_exit/cleanup), not progress dots alone. Environment failures before tests are separate from domain failures and baseline records.
