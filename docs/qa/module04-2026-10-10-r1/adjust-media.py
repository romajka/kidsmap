from pathlib import Path
p=Path(__file__).with_name('media.js');s=p.read_text(encoding='utf-8')
s=s.replace("await chooser.setFiles(assets+'/'+file);","await chooser.setFiles(Array.isArray(file)?file.map(f=>assets+'/'+f):assets+'/'+file);")
s=s.replace("await add('gallery1.png');await add('gallery2.png');","await add(['gallery1.png','gallery2.png']);")
p.write_text(s,encoding='utf-8')
print('QA uses native multiple-file picker.')
