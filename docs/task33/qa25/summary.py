"""Print bounded synthetic QA totals and failed check identifiers only."""
import json
import sys
from pathlib import Path
result = json.loads(Path(sys.argv[1]).read_text())
print(json.dumps({"rows": result["total"], "passed": result["passed"], "checks": len(result["checks"]), "checks_passed": result["checksPassed"], "failed_checks": [c for c in result["checks"] if not c["pass"]], "failed_rows": [{k: r[k] for k in ("file", "lang", "width", "issues")} for r in result["rows"] if r["issues"]], "events": result["events"]}, ensure_ascii=False))
