"""Bounded exact replacements for long template lines; fails on drift."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[3]
def edit(path,old,new):
    file=ROOT/path
    text=file.read_text(encoding='utf-8')
    assert text.count(old)==1,(path,old)
    file.write_text(text.replace(old,new,1),encoding='utf-8',newline='\n')
edit('src/catalog/templates/pages/includes/owner_place_continuous.html','  <form method="post" enctype="multipart/form-data" class="pw-form pc-form"',
    '''  {% if place_revision.review_note and place_revision.status == 'rejected' or place_revision.review_note and place_revision.status == 'declined' or place_revision.review_note and place_revision.status == 'draft' %}
  <section class="pc-review-note" data-place-review-note aria-labelledby="pc-review-note-title">
    <h2 id="pc-review-note-title">{{ ui.review_note_title }}</h2>
    <p>{{ place_revision.review_note }}</p>
  </section>
  {% endif %}
  <form method="post" enctype="multipart/form-data" class="pw-form pc-form"''')
path=ROOT/'static/css/pages/owner_place_continuous.css'
with path.open('a',encoding='utf-8',newline='\n') as file:
    file.write('\n.pc-review-note { margin-block: 1rem; padding: 1rem; border: 1px solid var(--pw-border, #d6ddd6); border-radius: 12px; }\n.pc-review-note h2 { margin: 0 0 .5rem; font-size: 1rem; }\n.pc-review-note p { margin: 0; white-space: pre-wrap; overflow-wrap: anywhere; }\n')
for lang,business,public in [('az','Biznes','İctimai məkan'),('en','Business','Public space')]:
    file=ROOT/f'locale/{lang}/LC_MESSAGES/django.po'
    text=file.read_text(encoding='utf-8')
    assert 'msgid "Бизнес"' not in text and 'msgid "Общественное место"' not in text
    file.write_text(text+f'\n#: src/catalog/models/catalog_structure.py\nmsgid "Бизнес"\nmsgstr "{business}"\n\n#: src/catalog/models/catalog_structure.py\nmsgid "Общественное место"\nmsgstr "{public}"\n',encoding='utf-8',newline='\n')
file=ROOT/'src/catalog/templates/pages/includes/permanent_place_map.html'
text=file.read_text(encoding='utf-8')
lines=text.splitlines()
for i,line in enumerate(lines):
    if 'data-locate-error=' in line: lines[i]='  data-locate-error="{{ ui.map_locate_error }}"\n  data-locating="{{ ui.map_locating }}"'
    if 'data-locate-unsupported=' in line: lines[i]='  data-locate-unsupported="{{ ui.map_locate_unsupported }}"'
file.write_text('\n'.join(lines)+'\n',encoding='utf-8',newline='\n')
edit('src/catalog/templates/pages/includes/permanent_place_map.html','data-map-status>','data-map-status role="status" aria-live="polite" aria-atomic="true">')
for path,old,new in [
 ('src/catalog/templates/pages/permanent_place_form.html',"owner_place_continuous.css' %}?v=20261007_place_r5","owner_place_continuous.css' %}?v=20261010_place_qa"),
 ('src/catalog/templates/pages/permanent_place_form.html',"owner_place_continuous.js' %}?v=20261007_place_r5","owner_place_continuous.js' %}?v=20261010_place_qa"),
 ('src/catalog/templates/pages/permanent_place_form.html','<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js">','<script data-owner-map-sdk="leaflet" src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js">'),
 ('src/catalog/templates/pages/permanent_place_form.html',"owner_place_map_picker.js' %}?v=3","owner_place_map_picker.js' %}?v=20261010_place_qa"),
 ('src/catalog/templates/includes/location_resolution.html','?v=20261009_map','?v=20261010_place_qa'),
 ('src/catalog/templates/admin/catalog/place/change_form.html',"kidsmap_place_form.css' %}?v=20261009_map","kidsmap_place_form.css' %}?v=20261010_place_qa"),
 ('src/catalog/templates/admin/catalog/place/change_form.html',"kidsmap_place_form.js' %}?v=20261009_map","kidsmap_place_form.js' %}?v=20261010_place_qa")]:edit(path,old,new)
print('Exact approved markup, cache versions and four PO entries updated.')
