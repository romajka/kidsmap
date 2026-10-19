from pathlib import Path
import json,sys,ast
R=Path('/mnt/c/kidsmap');Q=R/'.tmp/m13-full-r1';O=R/'docs/qa/module13-repair-2026-10-19-pc-r1';S=O/'stages/quality';S.mkdir(exist_ok=True);(S/'IMPLEMENTATION_PLAN.md').write_text((O/'QUALITY_PROFILE_PLAN.md').read_text())
def edit(path,old,new):
 b=(R/path).read_bytes();assert b.count(old)==1,path;return b.replace(old,new)
files={}
p='src/catalog/testcases/test_admin_review_workflow_fix.py';files[p]=edit(p,b"@override_settings(ADMIN_HOST='admin.audit.invalid', PUBLIC_BASE_URL='https://public.audit.invalid')",b"@override_settings(ADMIN_HOST='admin.audit.invalid', PUBLIC_BASE_URL='https://public.audit.invalid',\n                       ALLOWED_HOSTS=['admin.audit.invalid', 'public.audit.invalid'])")
p='src/catalog/testcases/test_moderation_sla.py';b=(R/p).read_bytes();ending=b'\r\n' if b'\r\n' in b else b'\n'
old="        review = PlaceReview.objects.create(place=self.place, text='Good place', status='pending')".encode();new="""        from django.contrib.auth import get_user_model
        from catalog.testcases.utils import create_quality_place
        from catalog.services.review_versions import submit_review
        author = get_user_model().objects.create_user('sla-review-author')
        review, candidate = submit_review(target=create_quality_place(), user=author,
                                         text='Good place', rating=5)""".replace('\n',ending.decode()).encode();assert b.count(old)==1;b=b.replace(old,new)
old=b"response = self.client.post(reverse('admin:catalog_placereview_approve', args=[review.pk]))";new=b"response = self.client.post(reverse('admin:catalog_placereview_approve', args=[review.pk]),"+ending+b"                                    {'revision_id': candidate.pk})";assert b.count(old)==1;files[p]=b.replace(old,new)
p='src/catalog/testcases/test_content_entry_final.py';b=(R/p).read_bytes();ending=b'\r\n' if b'\r\n' in b else b'\n';old=b'    setUp = EventAdminVersionTests.setUp';assert b.count(old)==1;new="""    def setUp(self):
        # TransactionTestCase flushes seed data left by migrations.
        from catalog.models import Category
        Category.objects.get_or_create(code='EDU', defaults={'name_az': 'QA Education'})
        EventAdminVersionTests.setUp(self)""".replace('\n',ending.decode()).encode();files[p]=b.replace(old,new)
def assertions(text):return [ast.dump(n,include_attributes=False) for n in ast.walk(ast.parse(text)) if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr.startswith('assert')]
proof={p:{'assertions_identical':assertions((R/p).read_text())==assertions(b.decode()),'count':len(assertions(b.decode()))} for p,b in files.items()};assert all(v['assertions_identical'] for v in proof.values());(S/'assertion-preservation.json').write_text(json.dumps(proof,indent=2))
for p in ['scripts/run_kidsmap_tests.sh','scripts/backup-db.sh']:files[p]=(R/p).read_bytes().replace(b'\r\n',b'\n')
assert not (R/'.gitattributes').exists();files['.gitattributes']=b'# Bash entry points must also run from Windows checkouts under WSL.\n*.sh text eol=lf\n'
p='.github/workflows/deploy.yml';b=(R/p).read_bytes();text=b.decode();a=text.index('  quality:');z=text.index('  deploy:',a)
quality='''  quality:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.12"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          sudo apt-get update
          sudo apt-get install --no-install-recommends -y gettext

      - name: Provision disposable Unix-socket PostgreSQL
        shell: bash
        run: |
          set -euo pipefail
          [[ "$GITHUB_RUN_ID" =~ ^[0-9]+$ && "$GITHUB_RUN_ATTEMPT" =~ ^[0-9]+$ ]]
          mkdir -p "$GITHUB_WORKSPACE/.tmp"
          profile_root=$(mktemp -d /tmp/kidsmap-task33-qa04-ci-XXXXXX)
          socket_root=$(mktemp -d "$GITHUB_WORKSPACE/.tmp/kidsmap-task33-qa04-socket-ci-XXXXXX")
          mkdir -m 0777 "$socket_root/socket"
          container_id=$(docker run -d --name "kidsmap-quality-$GITHUB_RUN_ID-$GITHUB_RUN_ATTEMPT" \
            --label "kidsmap.quality.run=$GITHUB_RUN_ID-$GITHUB_RUN_ATTEMPT" \
            --network none --mount "type=bind,source=$socket_root/socket,target=/qa-socket" \
            -e POSTGRES_USER=qa_stage04 -e POSTGRES_DB=qa_stage04 \
            -e POSTGRES_HOST_AUTH_METHOD=trust postgres:17-alpine \
            postgres -c listen_addresses= -k /qa-socket)
          printf '%s\\n' "$container_id" > "$profile_root/postgres-id"
          printf 'QUALITY_PROFILE_ROOT=%s\\nQUALITY_SOCKET_DIR=%s\\n' "$profile_root" "$socket_root/socket" >> "$GITHUB_ENV"
          for attempt in $(seq 1 60); do
            if docker exec "$container_id" pg_isready -h /qa-socket -U qa_stage04 -d qa_stage04; then break; fi
            sleep 1
          done
          docker exec "$container_id" pg_isready -h /qa-socket -U qa_stage04 -d qa_stage04

      - name: Complete isolated quality gate
        run: python scripts/run_isolated_quality.py --profile-root "$QUALITY_PROFILE_ROOT" --socket-dir "$QUALITY_SOCKET_DIR"

      - name: Remove only this job's PostgreSQL
        if: always() && env.QUALITY_PROFILE_ROOT != ''
        shell: bash
        run: |
          set -euo pipefail
          container_id=$(cat "$QUALITY_PROFILE_ROOT/postgres-id")
          actual=$(docker inspect --format '{{index .Config.Labels "kidsmap.quality.run"}}' "$container_id")
          [[ "$actual" == "$GITHUB_RUN_ID-$GITHUB_RUN_ATTEMPT" ]]
          docker rm --force "$container_id"

'''
new=text[:a]+quality+text[z:];assert new[new.index('  deploy:'):].encode()==text[z:].encode();files[p]=new.encode();(S/'deploy-job-preserved.json').write_text(json.dumps({'deploy_job_byte_identical':True,'quality_only':True},indent=2))
sys.path.insert(0,str(Q));from stage_apply import apply
apply('quality',files,'stages/quality/evidence/red-r1.json')
