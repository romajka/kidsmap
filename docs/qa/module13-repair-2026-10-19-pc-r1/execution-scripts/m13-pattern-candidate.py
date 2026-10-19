from pathlib import Path
import sys
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m13-full-r1';O=R/'docs/qa/module13-repair-2026-10-19-pc-r1';S=O/'stages/pattern';S.mkdir();(S/'IMPLEMENTATION_PLAN.md').write_text('CROSS-QA-02 followup: real DiscoverRunner stores an omitted pattern as None. Initial GREEN preserved 2 failing discovery assertions: legacy modules omitted. Normalize the default None alongside test*.py; retain explicit custom patterns. RED evidence cross/green-r1.json; same 41-method regression must pass, then full no-label inventory agreement.\n')
sys.path.insert(0,str(Q));from stage_apply import apply
p='src/config/test_runner.py';b=(R/p).read_bytes();needle=b'if self.pattern == "test*.py":';assert b.count(needle)==1
apply('pattern',{p:b.replace(needle,b'if self.pattern in (None, "test*.py"):')},'stages/cross/evidence/green-r1.json')
