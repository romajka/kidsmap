from pathlib import Path
import sys
raw=Path(sys.argv[1]).read_text()
for block in raw.split('='*70):
    if 'FAIL:' not in block and 'ERROR:' not in block:continue
    lines=block.splitlines()
    print(next(line for line in lines if line.startswith(('FAIL:','ERROR:'))))
    trace=[line for line in lines if '/src/catalog/testcases/' in line or line.lstrip().startswith(('self.assert','place =','form.save','self.approve'))]
    print('\n'.join(trace))
    errors=[line for line in lines if line.startswith(('AssertionError:', 'KeyError:', 'django.core.exceptions.', 'catalog.models.', 'AttributeError:'))]
    print('\n'.join(line[:700] for line in errors))
