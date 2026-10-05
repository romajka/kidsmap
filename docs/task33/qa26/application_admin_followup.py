"""Reuse unchanged matrix assertions for the CSS-only administrative delta."""
from pathlib import Path
root=Path(__file__).resolve().parent
source=(root/'application_matrix.js').read_text()
begin=source[:source.index("phase='private_boundary'")]
begin=begin.replace("const surfaces={create:'owner',edit:'owner',physical:'public',past:'public',cancelled:'public',rescheduled:'public',online:'public',landing:'public'};","const surfaces={};")
begin=begin.replace("if(lang==='ru'&&[390,1440].includes(width))","if(lang==='ru'&&[320,360,390,1440].includes(width))")
tail=source[source.index("if(includeAdmin){\n phase='admin_publish'"):]
(root/'application_admin_followup.js').write_text(begin+tail)
print('Bounded administrative matrix retains source assertions and actual publication flow')
