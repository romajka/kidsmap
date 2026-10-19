from pathlib import Path
import sys,json,ast
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m13-full-r1';O=R/'docs/qa/module13-repair-2026-10-19-pc-r1';S=O/'stages/ciunits';S.mkdir(exist_ok=True);(S/'IMPLEMENTATION_PLAN.md').write_text((O/'QUALITY_PROFILE_PLAN.md').read_text());files={}
p='scripts/tests/test_build_isolated_locales.py';b=(R/p).read_bytes();needle=b"'--compiler','wsl'";assert b.count(needle)==7;new=b.replace(needle,b"'--compiler','wsl' if os.name == 'nt' else 'native'")
asserts=lambda x:[ast.dump(n,include_attributes=False) for n in ast.walk(ast.parse(x)) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr.startswith('assert')]
assert asserts(b.decode())==asserts(new.decode());files[p]=new
p='.github/workflows/deploy.yml';b=(R/p).read_bytes();needle=b'      - name: Provision disposable Unix-socket PostgreSQL';assert b.count(needle)==1
extra='''      - name: Standalone Python checks
        run: python -m unittest discover -s scripts/tests -p 'test_*.py' -v

      - name: Set up Node
        uses: actions/setup-node@v4
        with:
          node-version: "24"

      - name: JavaScript unit and DOM checks
        shell: bash
        run: |
          set -euo pipefail
          npm install --prefix .tmp/phone-dom --no-save --package-lock=false jsdom@29.1.1
          export NODE_PATH="$PWD/.tmp/phone-dom/node_modules"
          export KIDSMAP_JSDOM="$NODE_PATH/jsdom"
          units=()
          for file in scripts/test_*.cjs scripts/tests/*.test.cjs static/js/tests/*.test.js; do
            case "$file" in
              scripts/test_localized_place_urls.cjs|scripts/test_review_submission.cjs|scripts/test_review_cooldown.cjs)
                # Require synthetic authenticated browser fixtures; accepted separately.
                continue ;;
            esac
            units+=("$file")
          done
          node --test "${units[@]}"

'''
files[p]=b.replace(needle,extra.encode()+needle)
raw=json.loads((O/'evidence/python-standalone.json').read_text());red={'exit':raw['exit'],'failures':[l for l in raw['summary'] if l.startswith('FAIL:')],'errors':[],'source':'Original unmodified Linux standalone run; wsl compiler and CRLF failure before repair.'};assert red['exit']==1 and red['failures'];(S/'evidence').mkdir();(S/'evidence/red-r1.json').write_text(json.dumps(red,indent=2));(S/'assertion-preservation.json').write_text(json.dumps({'file':'scripts/tests/test_build_isolated_locales.py','all_assertions_identical':True,'count':len(asserts(new.decode()))},indent=2))
sys.path.insert(0,str(Q));from stage_apply import apply
apply('ciunits',files,'stages/ciunits/evidence/red-r1.json')
