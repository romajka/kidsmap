"""Build only stage28 browser collectors from verified earlier CLI patterns."""
from pathlib import Path

root = Path(__file__).resolve().parents[1]
out = root / 'qa28'
families = {
    'r1': ('qa23/browser_bridge/commands.py', 'qa23/browser-matrix.js', 'qa23', '8783'),
    'specialist': ('qa25/application_bridge/commands.py', 'qa25/application_matrix.js', 'qa25', '8785'),
    'event': ('qa27/application_bridge/commands.py', 'qa27/application_matrix.js', 'qa27', '8787'),
}
for family, (bridge, matrix, prefix, port) in families.items():
    folder = out / ('browser_' + family + '_bridge')
    folder.mkdir(exist_ok=True)
    (folder / '__init__.py').write_text('', encoding='utf-8')
    code = (root / bridge).read_text(encoding='utf-8').replace(port, '8788').replace('/' + prefix + '/', '/qa28/')
    (folder / 'commands.py').write_text(code, encoding='utf-8')
    code = (root / matrix).read_text(encoding='utf-8').replace(port, '8788').replace('/' + prefix + '/', '/qa28/')
    code = code.replace('__QA' + prefix[2:] + '_EVIDENCE__', '__QA28_EVIDENCE__')
    (out / ('browser_' + family + '_matrix.js')).write_text(code, encoding='utf-8')
