# Ingress optional metadata and numeric parsing

Fresh3-method RED:3failure observations/0errors; valid domain-only privacy control passes. Newly confirmed canonical12: Unicode superscript isdigit() passes but int() raises, and oversized numeric string raises conversion limit; API500 instead of400. Newly confirmed13: malformed optional Referer with a valid Origin raises urlsplit ValueError after origin verification; API500 instead of accepting a valid event with empty optional domain.

Files exactly: controllers/tracking_controller.py catches only ValueError/OverflowError while parsing numeric place ID and returns existing invalid_payload400. services/tracking.py catches ValueError for optional referrer_domain only, keeping domain-only180limit and no URL/query/credentials. Add testcases/test_module12_payload.py unchanged from fresh RED. Do not broadly catch catalog/ACL/programming errors, change visibility, trust client dimensions, or relax original assertions. Existing invalid JSON/origin/rate/taxonomy/privacy cases remain.

Acceptance: Unicode and5000-digit payload400/no event, malformed optional referrer200/empty domain, valid userinfo/query referrer stores only hostname; fresh backend existing+new tracking/owner/AI, native endpoint success/failure plus final aggregate/privacy regression.
