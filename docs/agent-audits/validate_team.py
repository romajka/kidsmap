"""Offline structural checks for the KidsMap agent system; never imports Django."""
import json
from pathlib import Path
import re
import subprocess
import tomllib

ROOT = Path(__file__).resolve().parents[2]
REQUIRED = {
    "ROLE", "MISSION", "SCOPE", "READ FIRST", "SOURCE OF TRUTH", "TOOLS",
    "OPERATING RULES", "ALLOWED CHANGES", "FORBIDDEN CHANGES", "WORKFLOW",
    "CHECKLIST", "TEST REQUIREMENTS", "HANDOFF RULES", "ESCALATION", "OUTPUT CONTRACT",
}


def main():
    registry = json.loads((ROOT / ".agents/registry.json").read_text())
    active = registry["active"]
    ids = {role["id"] for role in active}
    issues = []
    if len(ids) != len(active) or not 8 <= len(ids) <= 12:
        issues.append("Roster count/uniqueness")
    inactive = {role["id"] for role in registry["inactive_retained"]}
    if ids & inactive:
        issues.append("Active/inactive overlap")
    checked_docs = set()
    for role in active:
        path = ROOT / role["definition"]
        text = path.read_text()
        headings = re.findall(r"^# (.+)$", text, re.M)
        if REQUIRED - set(headings) or len(headings) != len(set(headings)):
            issues.append(f"{role['id']}: missing or duplicate sections")
        native = tomllib.loads((ROOT / role["native_definition"]).read_text())
        if native.get("name") != role["id"] or not native.get("description"):
            issues.append(f"{role['id']}: native metadata mismatch")
        if role["definition"] not in native.get("developer_instructions", ""):
            issues.append(f"{role['id']}: missing canonical loader")
        if set(native) != {"name", "description", "developer_instructions"}:
            issues.append(f"{role['id']}: unexpected runtime overrides")
        checked_docs.add(path)
    native_names = {p.stem for p in (ROOT / ".codex/agents").glob("*.toml")}
    if native_names != ids:
        issues.append("Native roster differs from registry")
    workflows = list((ROOT / ".agents/workflows").glob("*.md"))
    if len(workflows) != 7:
        issues.append("Expected seven workflows")
    for path in workflows:
        text = path.read_text()
        for label in ("Lead:", "Support:", "Verification:"):
            if label not in text:
                issues.append(f"{path.name}: missing {label}")
        checked_docs.add(path)
    checked_docs.update(ROOT / p for p in (
        ".agents/README.md", ".agents/rules/engineering-contract.md",
        ".agents/knowledge/current-snapshot.md", ".agents/knowledge/pricing.md",
        ".agents/knowledge/schedule.md", ".agents/knowledge/permissions.md",
    ))
    for path in sorted(checked_docs):
        for dest in re.findall(r"\]\(([^)]+)\)", path.read_text()):
            if "://" in dest or dest.startswith("#"):
                continue
            target = path.parent / dest.split("#", 1)[0]
            if not target.exists():
                issues.append(f"{path.relative_to(ROOT)}: broken link {dest}")
    changed = subprocess.check_output(
        ["git", "diff", "--name-only", "HEAD"], cwd=ROOT, text=True
    ).splitlines()
    unknown = subprocess.check_output(
        ["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, text=True
    ).splitlines()
    allowed = (".agents/", ".codex/", "docs/agent-audits/")
    for path in changed + unknown:
        if path != ".codex" and not path.startswith(allowed):
            issues.append(f"Outside authorized agent-system scope: {path}")
    preserved = [f".agents/agents/{name}" for name in inactive] + ["kidsmap_extra_agents"]
    if subprocess.run(["git", "diff", "--quiet", "HEAD", "--", *preserved], cwd=ROOT).returncode:
        issues.append("Retained roles/package modified")
    placeholder = ROOT / ".agents/rules/history/codex-empty-placeholder-before-20260908"
    if not placeholder.is_file() or placeholder.stat().st_size != 0:
        issues.append("Original empty .codex placeholder not preserved")
    print(json.dumps({
        "active_roles": len(ids), "native_adapters": len(native_names),
        "required_sections": len(REQUIRED), "workflows": len(workflows),
        "checked_docs": len(checked_docs), "issues": issues,
    }, ensure_ascii=False, indent=2))
    return bool(issues)


if __name__ == "__main__":
    raise SystemExit(main())
