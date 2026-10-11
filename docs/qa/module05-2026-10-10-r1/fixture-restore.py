"""Only initial empty synthetic venue; offering transitions are native UI."""
from pathlib import Path
here=Path(__file__).resolve().parent
source=(here/'fixture-add.py').read_text(encoding='utf-8').replace("['localfresh']", "['restore']").replace('Uydurma fresh','Uydurma restore initial').replace('synthetic-fresh.png','synthetic-restore.png')
exec(compile(source,str(here/'fixture-add.py'),'exec'))
