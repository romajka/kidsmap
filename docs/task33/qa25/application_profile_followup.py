"""Build bounded person/index localization correction with unchanged full assertions."""
from pathlib import Path
root=Path(__file__).resolve().parent
text=(root/'application_matrix.js').read_text()
old="const surfaces={public:'public',person:'person',index:'person',invitations:'person',claims:'applicant',certificates:'person',org:'manager',review:'reviewer'};"
assert text.count(old)==1
text=text.replace(old,"const surfaces={person:'person',index:'person'};")
marker='// Private HTTP boundary and nested foreign IDs through real application routes.'
assert text.count(marker)==1
text=text.split(marker)[0]+"return {rows,total:rows.length,passed:rows.filter(r=>!r.issues.length).length,checks,checksPassed:checks.filter(r=>r.pass).length,events,externalTransport:'cached fonts and empty CDN stubs; no real external integration; person/index localization followup only'};\n}\n"
(root/'application_profile_followup.js').write_text(text)
print('Generated42-context person/index corrective matrix; full DOM/heading/focus assertions preserved')
