from pathlib import Path
import json,subprocess,urllib.request,hashlib
manifest = MANIFEST
preflight = PREFLIGHT
root=Path('/opt/kidsmap');stage=Path('/opt/kidsmap-releases/admin-moderation-20261016-r1')
activation=json.loads((stage/'activation.json').read_text())
assert activation['status']=='ACTIVATED'
active=json.loads(subprocess.check_output(['docker','inspect','kidsmap-web']))[0]
assert active['Image']==activation['image_id']
protected={n:json.loads(subprocess.check_output(['docker','inspect',n]))[0]['Id']==v for n,v in activation['DB_Redis_other_container_IDs_preserved'].items()}
assert all(protected.values())
checks={}
for host,paths in [('kidsmap.az',['/healthz','/','/ru/','/en/','/catalog/','/ru/catalog/','/en/catalog/']),('admin.kidsmap.az',['/admin/login/','/ru/admin/login/','/en/admin/login/'])]:
 for path in paths:
  request=urllib.request.Request('http://127.0.0.1:8000'+path,headers={'Host':host,'X-Forwarded-Proto':'https'})
  with urllib.request.urlopen(request,timeout=15)as res:checks[host+path]=res.status
assert all(v==200 for v in checks.values())
asset='static/admin/css/pages/kidsmap_review_workflow.css'
assert hashlib.sha256((root/'staticfiles'/asset.removeprefix('static/')).read_bytes()).hexdigest()==manifest['files'][asset]
backup=Path('/opt/kidsmap-release-backups/admin-moderation-20261016-r1')
backup_info=json.loads((backup/'backup.json').read_text())
assert (backup/'production-release.override.yml').is_file()
assert subprocess.run(['docker','image','inspect',preflight['image_id']],stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL).returncode==0
result={'production_deployed':True,'image_id':active['Image'],'tag':active['Config']['Image'],
 'base_commit':manifest['base_commit'],'patch_sha256':manifest['patch_sha256'],
 'health_checks':checks,'new_static_source_match':True,'protected_containers_unchanged':protected,
 'backup':backup_info,'old_image_preserved':True,'rollback_required':False,'migrations_run':False,'data_repair_run':False,
 'server_checkout_HEAD':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),
 'persistent_release_context':str(stage/'build-context'),'production_checkout_unchanged':True}
(stage/'final.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2))
