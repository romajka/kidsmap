from pathlib import Path
p=Path(__file__).with_name('inspect.js');s=p.read_text(encoding='utf-8').replace("p.locator('main').innerText()","p.locator('main').last().innerText()");p.write_text(s,encoding='utf-8')
