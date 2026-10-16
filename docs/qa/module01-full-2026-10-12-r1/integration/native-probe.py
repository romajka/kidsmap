import pathlib,subprocess,json,sys,gettext
root=pathlib.Path.cwd();scratch=root/'.tmp/module01-full-2026-10-12-r1/integration/native-probe';source=scratch/'source';po=source/'az/LC_MESSAGES/django.po';po.parent.mkdir(parents=True)
po.write_text('msgid ""\nmsgstr ""\n"Content-Type: text/plain; charset=UTF-8\\n"\n"Plural-Forms: nplurals=2; plural=(n != 1);\\n"\n\nmsgid "Hello"\nmsgstr "Salam"\n',encoding='utf8')
cmd=[sys.executable,str(root/'scripts/build_isolated_locales.py')];out=[]
def run(args,expected):
 r=subprocess.run(cmd+args,capture_output=True,text=True);out.append({'argv':cmd+args,'exit':r.returncode,'expected_zero':expected});assert (r.returncode==0)==expected
run(['build','--source-locale',str(source),'--output',str(scratch/'build'),'--locales','az','--compiler','native'],True)
run(['verify','--source-locale',str(source),'--manifest',str(scratch/'build/manifest.json')],True)
with (scratch/'build/locale/az/LC_MESSAGES/django.mo').open('rb') as f: assert gettext.GNUTranslations(f).gettext('Hello')=='Salam'
po.write_text(po.read_text().replace('Salam','Other'),encoding='utf8')
run(['verify','--source-locale',str(source),'--manifest',str(scratch/'build/manifest.json')],False)
(root/'docs/qa/module01-full-2026-10-12-r1/integration/native-probe.json').write_text(json.dumps({'checks':4,'commands':out,'scope':'native supplementary evidence; unchanged original WSL suite remains ENV failures'},indent=2))
print('native supplementary probe 4/4')
