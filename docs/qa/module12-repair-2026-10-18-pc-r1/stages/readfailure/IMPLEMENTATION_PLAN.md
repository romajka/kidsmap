# ANALYTICS-QA-14 — independent read failures

Fresh3-method RED:3failures/0errors. Healthy core catalog and GA, simulated actual local aggregate read DatabaseError gives owner500 and adminGA500; real SQL read error poisons outer transaction. Initial583-method broad run passed before this newly expanded fault coverage; preserve it as earlier snapshot, do not label it final after source change.

Modify only services/analytics_metrics.py and add testcases/test_module12_read_failure.py. Public build_subject_metrics keeps existing unsupported-type/disabled gate, invokes unchanged aggregation in a private _build_subject_metrics within transaction.atomic, catches DatabaseError outside savepoint and returns AnalyticsSummary(available=False), constant safe warning only. No fallback zero, no fake data, no catch around core catalog/ACL/GA reads or programming errors, no metric-definition change. Existing owner unavailable branch and independent GA use the result without other application changes.

Acceptance: owner200/explicit notice/no grid, GA200/selected90KPI unchanged/local unavailable, real SQL savepoint recovery with usable catalog; healthy22acceptance metrics/session/role/history tests unchanged. Fresh new targeted GREEN, real native SIMULATED read-fault owner/admin, then current-source full regression on a new own DB. User authorization already covers related fixes.
