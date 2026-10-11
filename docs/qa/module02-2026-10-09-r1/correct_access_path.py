from pathlib import Path
p=Path(__file__).with_name('access-proof.js');s=p.read_text(encoding='utf-8').replace('/account/place/','/account/places/').replace("'/place/'", "'/places/'")
p.write_text(s,encoding='utf-8')
