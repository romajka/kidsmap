import hashlib,json
from pathlib import Path
R=Path('/mnt/c/kidsmap');O=Path(__file__).resolve().parent;Q=R/'.tmp/site15-pc-fix-r1'
run=json.loads((O/'evidence/browser-green-matrix.json').read_text());assert len(run['rows'])==72 and not run.get('error')
p=R/'src/catalog/templates/admin/catalog/shared_settings_change_form.html';before=p.read_bytes();s=before.decode().replace('\r\n','\n')
old='''            <strong>{% translate "Форма содержит ошибки" %}.</strong>
            <span>
              {% blocktranslate count counter=errors|length %}
                Исправьте проблему ниже и сохраните карточку ещё раз.
              {% plural %}
                Исправьте проблемы ниже и сохраните карточку ещё раз.
              {% endblocktranslate %}
            </span>
            {{ adminform.form.non_field_errors }}
            {% if km_settings_conflict %}
              <p><a href="{{ km_settings_current_url }}" target="_blank" rel="noopener noreferrer">{% translate "Открыть текущую версию в новой вкладке" %}</a></p>
              {% if km_settings_reselect_files %}<p>{% translate "Выбранные файлы нужно выбрать заново перед повторным сохранением." %}</p>{% endif %}
            {% endif %}'''
new='''            {% if km_settings_conflict %}
              <span class="km-place-form-alert__icon" aria-hidden="true">!</span>
              <div class="km-place-form-alert__content">
                <strong class="km-place-form-alert__heading">{% translate "Форма содержит ошибки" %}.</strong>
                {{ adminform.form.non_field_errors }}
                <p class="km-place-form-alert__description"><a href="{{ km_settings_current_url }}" target="_blank" rel="noopener noreferrer">{% translate "Открыть текущую версию в новой вкладке" %}</a></p>
                {% if km_settings_reselect_files %}<p class="km-place-form-alert__description">{% translate "Выбранные файлы нужно выбрать заново перед повторным сохранением." %}</p>{% endif %}
              </div>
            {% else %}
              <strong>{% translate "Форма содержит ошибки" %}.</strong>
              <span>
                {% blocktranslate count counter=errors|length %}
                  Исправьте проблему ниже и сохраните карточку ещё раз.
                {% plural %}
                  Исправьте проблемы ниже и сохраните карточку ещё раз.
                {% endblocktranslate %}
              </span>
              {{ adminform.form.non_field_errors }}
            {% endif %}'''
assert old in s;s=s.replace(old,new,1)
(O/'template-initial-candidate.html').write_bytes(before)
p.write_bytes(s.replace('\n','\r\n').encode() if b'\r\n' in before else s.encode())
source=json.loads((Q/'expected-source.json').read_text());source['sources'][p.relative_to(R).as_posix()]=hashlib.sha256(p.read_bytes()).hexdigest();(Q/'expected-source.json').write_text(json.dumps(source,indent=2))
(O/'template-refinement.json').write_text(json.dumps({'file':p.relative_to(R).as_posix(),'before_sha256':hashlib.sha256(before).hexdigest(),'after_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'reason':'Rendered alert CSS is a two-column grid:30px icon + content. Initial direct strong/span/ul/p children occupied wrong grid cells. Conflict-only markup now uses existing icon/content classes. No CSS/JS/model/policy change.','initial_smoke_png':'png/smoke-content-ru-390-disjoint-conflict.png','original_full_matrix_retained':True},indent=2))
print('Conflict-only markup corrected to existing icon/content grid contract in approved template; original artifacts retained')
