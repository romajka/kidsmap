from pathlib import Path
p=Path(__file__).resolve().parent
(p/'map-smoke.js').write_text((p/'map-browser.js').read_text(encoding='utf-8').replace("['ru','az','en']","['ru']").replace('[360,390,768,1024,1280,1440]','[390]'),encoding='utf-8')
