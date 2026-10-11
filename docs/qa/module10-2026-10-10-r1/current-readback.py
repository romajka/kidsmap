"""Read-only current native candidate state, preserve entry readback."""
from pathlib import Path
P=Path(__file__).resolve().parent
source=(P/'organization-readback.py').read_text(encoding='utf-8').replace("'organization-readback.json'","'current-organization-readback.json'")
exec(compile(source,str(P/'organization-readback.py'),'exec'))
