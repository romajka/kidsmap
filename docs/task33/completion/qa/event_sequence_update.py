"""One-time QA ordering correction: draft saves precede actual publication."""
from pathlib import Path
p=Path(__file__).with_name('browser_event_matrix.js');s=p.read_text()
start=s.index("for(const language of ['az','ru','en']){")
end=s.index('return {runtime:fixtures.runtime',start)
block=s[start:end]
assert "phase='localized_save_notice_'" in block
s=s[:start]+s[end:]
anchor="if(includeAdmin){\n phase='admin_publish'"
assert s.count(anchor)==1
s=s.replace(anchor,block+anchor)
p.write_text(s)
print('Native localization saves now precede publication; assertions unchanged')
