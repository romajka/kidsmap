"""Extract Playwright CLI structured results without copying raw browser records into Git."""
import json
import sys
from pathlib import Path

root = Path(sys.argv[1])
raw = (root / "result-cli.txt").read_text()
start = raw.find("### Result")
if start < 0:
    raise SystemExit("Playwright result missing; inspect external evidence")
payload = raw[start + len("### Result"):].split("###", 1)[0].strip()
result = json.loads(payload)
(root / "results.json").write_text(json.dumps(result, ensure_ascii=False, indent=2))
print(json.dumps({"rows": result["total"], "passed": result["passed"], "checks": len(result["checks"]), "checks_passed": result["checksPassed"], "errors": len(result["events"]["errors"]), "failed_requests": len(result["events"]["failed"]), "external_requests": len(result["events"]["external"])}))
if result["passed"] != result["total"] or result["checksPassed"] != len(result["checks"]) or any(result["events"].values()):
    raise SystemExit(1)
