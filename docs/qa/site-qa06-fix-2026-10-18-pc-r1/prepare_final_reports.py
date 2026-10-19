import hashlib,json
from pathlib import Path
O=Path(__file__).resolve().parent;sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for name in ['finalize.py','build_report.py']:
 p=O/name;s=p.read_text();assert "'browser-permissions'" in s;s=s.replace("'browser-permissions'","'browser-final-permissions'");p.write_text(s)
p=O/'build_report.py';s=p.read_text();needle='## Preservation and limits';s=s.replace(needle,'''The first authority harness reused one BrowserContext across forced fixture-role changes. After a native add-only upload, a late media response deleted that context's session cookie: the proxy-only actor landed on login, producing16partial rows/35checks with5false permission assertions and then a missing-input timeout. This failed run remains [retained](evidence/browser-permissions.json). Actor flags/direct permissions are correct; a [fresh-context control](evidence/browser-proxy-fresh.json) gives footer200/hub403, and the [race reproduction](evidence/browser-auth-race.json) observes a media response deleting the cookie (values never recorded). The final harness creates a fresh context per actor and disables API redirect following; original authority/no-write expectations are retained. Final35rows/76checks PASS. No application or permission change was made for this fixture race. [Harness refinement](permission-harness-refinement.json). Already-passing editor cases were not rerun.

## Preservation and limits''')
s=s.replace('Read-only repo/RW own scratch/internal QA network.', '''Read-only repo/RW own scratch/internal QA network. After the full upload matrix, normal synthetic media were copied byte-for-byte into `/tmp/site06-pc-fix-r1-media` in the same app's existing64MiB tmpfs. All452original/copied hashes match; original host media remain. Only owned QA settings/static assertion select this literal root before import; application settings/DB/media URLs stay unchanged. Every snapshot still fully reads and hashes files without caching. Final530synthetic media files were exported to own ignored scratch with identical SHA and must match the final HTTP fixture. [Handoff](evidence/media-storage-handoff.json), [final export](evidence/media-final-manifest.json).''')
p.write_text(s)
review={
 'reviewed':True,'method':'Actual native PNGs opened with view_image by /root; inline review, no independent reviewer claim',
 'images':[
  {'path':'png/branding-rejected-content-az-390.png','classification':'initial defect retained','observation':'Heading grid readable but inline long error grows already overflowing file row; no final acceptance claim.'},
  {'path':'png/branding-rejected-content-ru-1440.png','classification':'initial defect retained','observation':'Long inline error extends past its section; existing form/sidebar layout remains outside scope.'},
  {'path':'png/smoke-final-branding-rejected-content-ru-390.png','classification':'pre-color correction','observation':'Wrapping summary and actual focused file input; old green link later measured3.66:1 and corrected.'},
  {'path':'png/final-branding-rejected-content-en-1440.png','classification':'pre-color complete behavior matrix','observation':'Readable grid and linked error; color utility remains the only later delta.'},
  {'path':'png/current-color-content-az-360.png','classification':'final current markup','observation':'Localized media error fits summary at360px, dark readable link, keyboard focus on file input. Existing field/help horizontal overflow and old Russian plural text remain SITE08/SITE11.'},
  {'path':'png/current-color-super-en-1440.png','classification':'final current markup','observation':'Dark error link, readable heading, stored preview retained; no broader layout closure.'},
  {'path':'png/analytics-rejected-en-1440.png','classification':'final current direct editor','observation':'Direct analytics shows localized media error and autofocus outline; draft value remains.'},
  {'path':'png/gallery-add-rejected-ru-390.png','classification':'final current gallery form','observation':'Image-field summary readable at390px; placement selection remains.'},
  {'path':'png/stale-bad-file-en-1440.png','classification':'final current stale form','observation':'409 retains draft, current stored preview, explicit new-tab recovery and file-reselection notice. Existing SITE15 link style is unchanged; contrast claim applies only to new media error links.'},
  {'path':'png/legacy-delete-confirm-390.png','classification':'final current compatibility','observation':'Real alertdialog and visible confirm/cancel on390px; deletion/retry results separately asserted.'},
 ],
 'current_new_error_link_min_contrast':min(r['geometry']['contrast'] for r in json.loads((O/'evidence/browser-color-forms.json').read_text())['rows']),
 'limits':'Viewport Chromium only; existing global form overflow/sidebar layout/old untranslated strings remain open. No physical-device/screenreader/global WCAG claim.'
}
for row in review['images']:row['sha256']=sha(O/row['path'])
(O/'visual-review.json').write_text(json.dumps(review,ensure_ascii=False,indent=2))
adjustments=json.loads((O/'qa-adjustments.json').read_text());adjustments.append({'kind':'fixture-role session reuse race, retained','initial':'browser-permissions.json:16rows35checks30PASS5false permission checks, then timeout on missing footer input','evidence':['fixture-authority.json','browser-proxy-fresh.json','browser-auth-race.json','permission-harness-refinement.json'],'observed':'Late media response deletes session cookie after forced role switch; fresh proxy context gives footer200/hub403','correction':'Fresh BrowserContext per actor and maxRedirects0 for API probes; unchanged application/permission/no-write expectations','final':'browser-final-permissions.json:35rows76PASS; no application change'})
(O/'qa-adjustments.json').write_text(json.dumps(adjustments,ensure_ascii=False,indent=2))
print(json.dumps({'visual_images_actually_reviewed':len(review['images']),'final_permission_suite_selected':True,'retained_fixture_race_documented':True}))
