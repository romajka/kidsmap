"""Re-evaluate retained DOM facts after correcting site-Organization selection."""
import copy
import json
import sys
from pathlib import Path
root = Path(sys.argv[1])
original = json.loads((root / 'matrix.json').read_text())
(root / 'matrix-original-validator.json').write_text(json.dumps(original, ensure_ascii=False, indent=2))
result = copy.deepcopy(original)
for row in result['rows']:
    row['issues'] = [issue for issue in row['issues'] if issue not in ('entity_schema', 'geography', 'currency', 'invented_entity_fact', 'closed_active_facts')]
    entity = next((item for item in row['schema'] if item.get('url') == row['canonical'] and item.get('@type') in ('LocalBusiness', 'Organization', 'Course')), None)
    if entity is None:
        row['issues'].append('entity_schema')
        continue
    expected_type = 'Organization' if row['kind'] == 'organization' else 'Course' if row['kind'] == 'activity' else 'LocalBusiness'
    if entity['@type'] != expected_type:
        row['issues'].append('entity_type')
    def currencies(value):
        if isinstance(value, dict):
            if 'priceCurrency' in value:
                yield value['priceCurrency']
            for child in value.values():
                yield from currencies(child)
        elif isinstance(value, list):
            for child in value:
                yield from currencies(child)
    if any(value != 'AZN' for value in currencies(entity)):
        row['issues'].append('currency')
    if row['kind'] in ('fallback', 'complete', 'closed') and entity.get('address', {}).get('addressCountry') != 'AZ':
        row['issues'].append('geography')
    if row['kind'] in ('organization', 'activity') and any(key in entity for key in ('aggregateRating', 'startDate', 'endDate', 'geo')):
        row['issues'].append('invented_entity_fact')
    if row['kind'] == 'closed' and any(key in entity for key in ('offers', 'openingHours')):
        row['issues'].append('closed_active_facts')
result['passed'] = sum(not row['issues'] for row in result['rows'])
result['validator_correction'] = 'Entity selected by canonical URL; base template site Organization is separate.'
(root / 'matrix-rechecked.json').write_text(json.dumps(result, ensure_ascii=False, indent=2))
summary = dict(passed=result['passed'], total=result['total'], failures=[{key:row[key] for key in ('width','lang','kind','issues')} for row in result['rows'] if row['issues']], legacy=result['legacy'], keyboard=result['keyboard'], console_errors=len(result['events']['errors']), request_failures=len(result['events']['failed']), bad_responses=len(result['events']['badResponses']))
(root / 'summary-rechecked.json').write_text(json.dumps(summary, indent=2))
print(json.dumps(summary))
